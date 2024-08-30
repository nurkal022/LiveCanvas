import streamlit as st
import requests
import base64
from PIL import Image
import io
from streamlit_drawable_canvas import st_canvas
import numpy as np
from const import LEONARDO_API_KEY

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

@st.cache_data
def generate_lcm_image(image_data, prompt, width, height, style="CINEMATIC", strength=0.65):
    url = "https://cloud.leonardo.ai/api/rest/v1/generations-lcm"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {LEONARDO_API_KEY}"
    }
    payload = {
        "width": width,
        "height": height,
        "imageDataUrl": f"data:image/jpeg;base64,{image_data}",
        "prompt": prompt,
        "style": style,
        "strength": strength
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['lcmGenerationJob']['imageDataUrl'][0]
    except requests.exceptions.Timeout:
        st.error("The request to the API timed out. Please try again later.")
    except requests.exceptions.ConnectionError as e:
        st.error(f"A connection error occurred: {e}")
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while making the request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            st.error(f"Response status code: {e.response.status_code}")
            st.error(f"Response content: {e.response.text}")
    except KeyError:
        st.error("Unexpected response format from the API.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
    return None

def main():
    st.set_page_config(layout="wide", page_title="Leonardo AI Image Generator", page_icon="🎨")
    
    # Применяем полностью темную тему
    st.markdown("""
    <style>
    /* Основной фон приложения */
    .stApp {
        background-color: #121212;
        color: #E0E0E0;
    }
    
    /* Боковая панель */
    .css-1d391kg {
        background-color: #1E1E1E;
    }
    
    /* Заголовки */
    h1, h2, h3 {
        color: #BB86FC;
    }
    
    /* Кнопки */
    .stButton>button {
        background-color: #BB86FC;
        color: #121212;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-size: 16px;
    }
    .stButton>button:hover {
        background-color: #3700B3;
        color: #E0E0E0;
    }
    
    /* Выпадающие списки */
    .stSelectbox>div>div>select {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border: 1px solid #BB86FC;
    }
    
    /* Текстовые поля ввода */
    .stTextInput>div>div>input {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border: 1px solid #BB86FC;
    }
    
    /* Слайдеры */
    .stSlider>div>div>div>div {
        background-color: #BB86FC;
    }
    
    /* Канвас */
    .stCanvas {
        background-color: #2D2D2D;
        border: 2px solid #BB86FC;
        border-radius: 8px;
    }
    
    /* Изображение результата */
    .output-image {
        border: 2px solid #BB86FC;
        border-radius: 8px;
    }
    
    /* Цветовой пикер */
    .stColorPicker>div>div>div {
        background-color: #2D2D2D;
        border: 1px solid #BB86FC;
    }
    
    /* Спиннер загрузки */
    .stSpinner>div>div>div {
        border-top-color: #BB86FC !important;
    }
    
    /* Разделители */
    hr {
        border-color: #BB86FC;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🎨 Sketch Vision Image Generation")

    # Боковое меню с параметрами
    with st.sidebar:
        st.header("🖌️ Canvas Settings")
        size_options = [
            "512x512", "768x768", "1024x1024", 
            "512x768", "768x512", "1024x768", "768x1024"
        ]
        selected_size = st.selectbox("Canvas size:", size_options)
        width, height = map(int, selected_size.split('x'))

        drawing_mode = st.selectbox(
            "Drawing tool:", ("freedraw", "line", "rect", "circle", "transform")
        )
        stroke_width = st.slider("Stroke width:", 1, 25, 3)
        
        st.subheader("🎨 Quick Color Selection")
        color_buttons = st.columns(4)
        colors = ["#000000", "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF", "#FFFFFF"]
        for i, color in enumerate(colors):
            if color_buttons[i % 4].button("", key=f"color_{color}", help=f"Select {color}"):
                st.session_state.stroke_color = color
            
            color_buttons[i % 4].markdown(
                f'<div style="width:30px;height:30px;background-color:{color};margin-top:5px;border-radius:50%;border:2px solid #BB86FC;"></div>',
                unsafe_allow_html=True
            )

        stroke_color = st.color_picker("Custom color:", st.session_state.get('stroke_color', '#FFFFFF'))
        st.session_state.stroke_color = stroke_color

        bg_color = st.color_picker("Background color:", "#2D2D2D")
        
        st.header("🖼️ Generation Settings")
        prompt = st.text_input("Enter your prompt:", "")
        style = st.selectbox("Choose style:", [
            "ANIME", "CINEMATIC", "CONCEPT_ART", "DYNAMIC", "ENVIRONMENT",
            "FANTASY_ART", "PAINTING", "PHOTOGRAPHY", "PRODUCT", "RAYTRACED",
            "SKETCH_BW", "SKETCH_COLOR", "VIBRANT", "NONE"
        ])
        strength = st.slider("Creativity Strength:", 0.0, 1.0, 0.65)

        if st.button('🧹 Clear Canvas'):
            st.session_state.canvas_key = st.session_state.get('canvas_key', 0) + 1
            st.session_state.pop('last_canvas_state', None)
            st.experimental_rerun()

    # CSS для фиксации размеров холста и изображения
    st.markdown(f"""
        <style>
        .stCanvas {{
            width: {width}px !important;
            height: {height}px !important;
            background-color: {bg_color} !important;
        }}
        .output-image {{
            width: {width}px !important;
            height: {height}px !important;
            object-fit: contain;
        }}
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎨 Drawing Canvas")
        
        bg_image = Image.new('RGB', (width, height), color=bg_color)
        img_array = np.array(bg_image)
        
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=stroke_width,
            stroke_color=st.session_state.stroke_color,
            background_image=Image.fromarray(img_array.astype('uint8')),
            height=height,
            width=width,
            drawing_mode=drawing_mode,
            key=f"canvas_{st.session_state.get('canvas_key', 0)}",
            update_streamlit=True,
        )
    
    with col2:
        st.subheader("🖼️ Generated Image")
        image_placeholder = st.empty()

    def check_changes_and_generate():
        if canvas_result.image_data is not None and canvas_result.json_data is not None:
            current_canvas_state = canvas_result.json_data
            current_prompt = prompt
            current_style = style
            current_strength = strength
            
            state_changed = (
                'last_canvas_state' not in st.session_state or
                st.session_state.last_canvas_state != current_canvas_state or
                st.session_state.get('last_prompt') != current_prompt or
                st.session_state.get('last_style') != current_style or
                st.session_state.get('last_strength') != current_strength
            )
            
            if state_changed:
                st.session_state.last_canvas_state = current_canvas_state
                st.session_state.last_prompt = current_prompt
                st.session_state.last_style = current_style
                st.session_state.last_strength = current_strength
                
                img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                img = img.convert('RGB')
                img_data = encode_image(img)
                
                with st.spinner("🔮 Generating image..."):
                    result = generate_lcm_image(img_data, current_prompt, width, height, current_style, current_strength)
                    
                    if result:
                        generated_image = Image.open(io.BytesIO(base64.b64decode(result.split(',')[1])))
                        image_placeholder.image(generated_image, caption="Generated Image", use_column_width=False, width=width, output_format="PNG", clamp=True)
                    else:
                        image_placeholder.error("❌ Failed to generate image. Please check the error messages above and try again.")

    check_changes_and_generate()
    
    st.markdown("""
    ### 📝 Instructions
    1. Use the sidebar to adjust canvas size and drawing tools.
    2. Choose a color from the quick color selection or use the custom color picker.
    3. Draw on the canvas using your mouse or touchpad.
    4. The image will be automatically generated as you draw.
    5. Adjust the prompt, style, and creativity strength in the sidebar to change the generated image.
    6. Use 'Clear Canvas' in the sidebar to start over with a blank canvas.
    """)

if __name__ == "__main__":
    main()
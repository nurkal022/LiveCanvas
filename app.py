import streamlit as st
import requests
import base64
from PIL import Image, ImageDraw
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
    st.set_page_config(layout="wide", page_title="Leonardo AI Image Generator")
    
    st.title("Leonardo AI LCM Image Generation")

    # Боковое меню с параметрами
    with st.sidebar:
        st.header("Canvas Settings")
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
        stroke_color = st.color_picker("Stroke color:", "#000000")
        bg_color = st.color_picker("Background color:", "#ffffff")
        
        st.header("Generation Settings")
        prompt = st.text_input("Enter your prompt:", "")
        style = st.selectbox("Choose style:", ["CINEMATIC", "DYNAMIC", "CREATIVE"])
        strength = st.slider("Creativity Strength:", 0.0, 1.0, 0.65)

        if st.button('Clear Canvas'):
            st.session_state.canvas_key = st.session_state.get('canvas_key', 0) + 1
            st.experimental_rerun()

    # CSS для фиксации размеров холста и изображения
    st.markdown(f"""
        <style>
        .stCanvas {{
            width: {width}px !important;
            height: {height}px !important;
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
        st.subheader("Drawing Canvas")
        
        # Создаем базовое изображение
        bg_image = Image.new('RGB', (width, height), color=bg_color)
        
        # Преобразуем изображение в массив numpy для st_canvas
        img_array = np.array(bg_image)
        
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            background_image=Image.fromarray(img_array.astype('uint8')),
            height=height,
            width=width,
            drawing_mode=drawing_mode,
            key=f"canvas_{st.session_state.get('canvas_key', 0)}",
            update_streamlit=True,  # Add this line
        )
    
    with col2:
        st.subheader("Generated Image")
        image_placeholder = st.empty()

    # Отслеживаем изменения на холсте
    if canvas_result.image_data is not None and canvas_result.json_data is not None:
        # Проверяем, изменился ли холст
        current_canvas_state = canvas_result.json_data
        if 'last_canvas_state' not in st.session_state or st.session_state.last_canvas_state != current_canvas_state:
            st.session_state.last_canvas_state = current_canvas_state
            
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            img = img.convert('RGB')
            img_data = encode_image(img)
            
            with st.spinner("Generating image..."):
                result = generate_lcm_image(img_data, prompt, width, height, style, strength)
                
                if result:
                    generated_image = Image.open(io.BytesIO(base64.b64decode(result.split(',')[1])))
                    image_placeholder.image(generated_image, caption="Generated Image", use_column_width=False, width=width, output_format="PNG", clamp=True)
                else:
                    image_placeholder.error("Failed to generate image. Please check the error messages above and try again.")
    
    st.markdown("""
    ### Instructions
    1. Use the sidebar to adjust canvas size and drawing tools.
    2. Draw on the canvas using your mouse or touchpad.
    3. The image will be automatically generated as you draw.
    4. Adjust the prompt, style, and creativity strength in the sidebar to change the generated image.
    5. Use 'Clear Canvas' in the sidebar to start over with a blank canvas.
    """)

if __name__ == "__main__":
    main()
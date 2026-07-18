import streamlit as st
import os
import requests
import json
import base64
from openai import OpenAI

# 1. Interface Opbouw
st.title("Generate Stickman Images For Your Videos")
st.write("The factory is running! Enter your API key, paste your script, and let's create.")

user_api_key = st.text_input("Paste your OpenAI API key here:", type="password")

quality_map = {
    "Medium quality": "standard",
    "High quality (may cost more Openai tokes)": "hd"
}
selection = st.selectbox("Choose your Image Quality:", list(quality_map.keys()))
kwaliteit = quality_map[selection]

script_text = st.text_area("Paste here your script: ", height=250)

# 2. De Fabriek Logica
if st.button("Generate"):
    if not user_api_key:
        st.error("Oops! Don't forget your API key.")
        st.stop()
    if not script_text:
        st.warning("Please paste your script in the box above.")
        st.stop()

    client = OpenAI(api_key=user_api_key)
    OUTPUT_DIR = "Gegeneerde_Film"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
   # STAP 1: AI Storyboard Agent met "Dynamische Pacing"
    with st.spinner("AI is analyzing script length to determine optimal scene count..."):
        try:
            # Dynamische berekening: 1 scene per 8 woorden is jouw ideale tempo.
            # We zetten een ondergrens (min 10) en bovengrens (max 100) voor veiligheid.
            word_count = len(script_text.split())
            target_scenes = max(15, min(100, word_count // 8)) 
            
            storyboard_prompt = (
                f"Analyze the following script: {script_text}\n\n"
                f"CRITICAL INSTRUCTION: Your target is to create approximately {target_scenes} scenes. "
                "This is a dynamic ratio: you must maintain the pace of 1 scene per 8 words. "
                "Break the script down into small, granular actions. "
                "If the script is short, keep it punchy. If the script is long, keep the pace consistent. "
                "Style: Minimalist stick figure illustration. "
                "Return a JSON list of scenes. Format: {'scenes': [{'description': 'detailed visual prompt'}]}. "
                "Do not include markdown formatting or extra text."
            )
            
            storyboard_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": storyboard_prompt}],
                response_format={ "type": "json_object" }
            )
            data = json.loads(storyboard_response.choices[0].message.content)
            scenes = data['scenes']
            st.write(f"Storyboard created with {len(scenes)} scenes (Calculated for optimal pace).")
        except Exception as e:
            st.error(f"Error creating storyboard: {e}")
            st.stop()

    # STAP 2: Generatie
    progress_bar = st.progress(0)
    
    for i, scene in enumerate(scenes):
        actie_prompt = scene["description"]
        bestandsnaam = f"{i+1:03d}_youtube.jpg"
        
        st.write(f"🎨 Generating image {i+1}: {actie_prompt}")
        
       # DALL-E prompt - Aangepast naar jouw specifieke stijlvereisten
        dalle_prompt = (
            "Generate a YouTube video illustration (16:9) . "
            "STYLE REQUIREMENTS: Simple 2D black line drawings, mostly white empty space . "
            "Pure white background, thick uneven black outlines, wobbly hand-drawn lines . "
            "Flat colors only . Very basic shapes and childish comic style . "
            "No realistic shading, no 3D, no cinematic lighting, no realistic cartoon style . "
            "Keep compositions extremely clear, simple, bold and centered . "
            f"OBJECTS AND ACTION TO DRAW: {actie_prompt}"
        )

        try:
            response = client.images.generate(
                model="gpt-image-2", 
                prompt=dalle_prompt, 
                size="1792x1024", 
                n=1
            )
            
            # Hier zit de fix: we controleren eerst wat we terugkrijgen
            image_data = response.data[0]
            doel_pad = os.path.join(OUTPUT_DIR, bestandsnaam)
            
            if hasattr(image_data, 'url') and image_data.url:
                # Als er een URL is, downloaden we deze
                img_data = requests.get(image_data.url).content
            elif hasattr(image_data, 'b64_json') and image_data.b64_json:
                # Als er base64 data is, decoderen we deze direct
                img_data = base64.b64decode(image_data.b64_json)
            else:
                raise Exception("Geen afbeelding ontvangen van de API.")
            
            # Opslaan en weergeven
            with open(doel_pad, 'wb') as handler:
                handler.write(img_data)
            
            st.image(doel_pad, caption=f"Scene {i+1}")
            
        except Exception as e:
            st.error(f"Error generating image {i+1}: {e}")

        progress_bar.progress((i + 1) / len(scenes))

    st.success("Production Finished! 🎉")

import zipfile
import io

# ... (jouw bestaande code waar je de plaatjes genereert en toont) ...

# 1. Zorg dat je een lijst hebt met de gegenereerde plaatjes (bijv. image_data_list)
# 2. Voeg dit toe onder je st.write/st.image gedeelte:

def create_zip(images):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for i, img_bytes in enumerate(images):
            zip_file.writestr(f"scene_{i+1}.png", img_bytes)
    return zip_buffer.getvalue()

# Stel dat 'image_bytes_list' een lijst is met de ruwe bytes van je plaatjes:
if 'image_bytes_list' in st.session_state and len(st.session_state.image_bytes_list) > 0:
    zip_data = create_zip(st.session_state.image_bytes_list)
    
    st.download_button(
        label="📥 Download All Scenes as ZIP",
        data=zip_data,
        file_name="storyboard.zip",
        mime="application/zip"
    )
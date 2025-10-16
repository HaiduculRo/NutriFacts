import json
import logging
import re

import cv2
import numpy as np
from openai import OpenAI
from sklearn.cluster import KMeans

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def preprocess_image_based_on_font(image, clusters=3):
    """
    Preprocesează imaginea adaptiv pe baza detecției fundal/text și optimizează pentru OCR.
    Returnează imaginea binarizată și tipul de text detectat (închis/deschis/ambiguu).
    """
    if image is None or image.size == 0:
        print("⚠️ Imaginea de intrare este invalidă!")
        return None, "invalid"

    # === Detectare fundal/text ===
    h, w = image.shape[:2]
    zoom_factor = 1.1
    center = (w // 2, h // 2)
    zoomed = cv2.getRectSubPix(image, (int(w / zoom_factor), int(h / zoom_factor)), center)
    small = cv2.resize(zoomed, (200, 200))
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    pixels = hsv.reshape(-1, 3)

    kmeans = KMeans(n_clusters=clusters, random_state=0).fit(pixels)
    centers = sorted(kmeans.cluster_centers_, key=lambda x: x[2], reverse=True)
    background, text = centers[0], centers[1] if clusters >= 2 else centers[0]
    h_txt, s_txt, v_txt = text

    if v_txt > 120:
        text_type = "text deschis"
    elif v_txt < 80:
        text_type = "text închis"
    else:
        text_type = "text ambiguu"

    print(f"🔸 Tip text estimat: {text_type} (V={v_txt:.0f})")

    # === Preprocesare reală ===
    # Păstrăm imaginea originală pentru calitate
    original = image.copy()
    
    # Convertim la grayscale pentru procesare
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 1. Ajustare contrast/luminozitate (cu parametri mai conservatori)
    adjusted = cv2.convertScaleAbs(gray, alpha=0.6, beta=50)

    # 2. Detecție highlights (pixeli > 240) și estompare subtilă
    mask_highlight = cv2.inRange(adjusted, 240, 255) 
    blurred = cv2.GaussianBlur(adjusted, (5, 5), 0)  # Kernel mai mic pentru păstrarea detaliilor
    adjusted[mask_highlight > 0] = blurred[mask_highlight > 0]

    # 3. CLAHE pentru contrast local adaptiv (cu parametri mai conservatori)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast_img = clahe.apply(adjusted)

    # 4. Denoising subtil
    denoised = cv2.fastNlMeansDenoising(contrast_img, h=10, templateWindowSize=7, searchWindowSize=21)

    # 5. Binarizare adaptivă
    _, final = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return final, text_type

def clean_and_structure_text(text):
    """
    Utilizează GPT pentru a curăța textul extras și pentru a-l structura într-un JSON cu atribute nutriționale.
    """

    prompt = f"""
    Extract the following nutritional information from the text below and structure it as a JSON.
    Follow these important rules:
    
    1. Convert all values to per 100g. If you see values per serving, use the serving size to calculate per 100g.
    2. Pay careful attention to units (mg vs g):
       - 1g = 1000mg
       - Convert all mg values to g by dividing by 1000
       - Example: 500mg sodium = 0.5g sodium_100g
    3. "Total Carbohydrate(s)" or "Total Carb" should be extracted as "carbohydrates_100g"
    4. Extract both the original serving size AND the per 100g values
    
    Extract these fields:
    - serving_size (text description of serving size, e.g. "1 cup (245g)")
    - servings_per_container (number of servings in the package)
    - fat_100g (default 0 if missing)
    - saturated-fat_100g (default 0 if missing)
    - trans-fat_100g (default 0 if missing)
    - cholesterol_100g (default 0 if missing, convert from mg)
    - sodium_100g (default 0 if missing, convert from mg)
    - carbohydrates_100g (default 0 if missing, this is "Total Carbohydrate")
    - fiber_100g (default 0 if missing)
    - sugars_100g (default 0 if missing)
    - proteins_100g (default 0 if missing)
    - nutri_score (default 0 if missing)
    
    Text: "{text}"
    """
    try:
        # Inițializăm clientul OpenAI
        client = OpenAI(api_key="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")
        logger.info(text)
        
        # Apel GPT
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in nutritional data extraction."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extragem conținutul raw
        raw_result = response.choices[0].message.content.strip()
        
        # Scoatem eventualii backticks ```json ... ```
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", raw_result, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Dacă nu găsim backticks, presupunem că răspunsul este doar JSON
            json_str = raw_result
        
        # Parse JSON-ul curat
        result = json.loads(json_str)
        return result

    except Exception as e:
        logger.warning(f"⚠️ Eroare la extragerea datelor cu GPT: {e}")
        return None 
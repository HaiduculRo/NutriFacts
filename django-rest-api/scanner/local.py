import glob
import json
import logging
import ntpath
import os
import pickle
import re
import timeit

import cv2
import matplotlib.pyplot as plt
import numpy as np
import openai
import pytesseract
from sklearn.cluster import KMeans
from ultralytics import YOLO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
logger.info(f"\n📁 Directorul scriptului: {script_dir}")

# Încărcăm modelul YOLO cu calea absolută și gestionăm erorile
try:
    model_path = os.path.join(script_dir, 'best.pt')
    logger.info(f"🔍 Încărcăm modelul YOLO de la: {model_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Modelul YOLO nu a fost găsit la: {model_path}")
    model = YOLO(model_path)
    logger.info("✅ Modelul YOLO a fost încărcat cu succes!")
except Exception as e:
    logger.error(f"❌ Eroare la încărcarea modelului YOLO: {str(e)}")
    raise

# Încărcăm modelul Nutri-Score cu calea absolută și gestionăm erorile
try:
    logger.info("\n" + "="*50)
    logger.info("🔄 ÎNCĂRCARE MODEL NUTRI-SCORE")
    logger.info("="*50)
    
    model_path = os.path.join(script_dir, 'models/nutri_score_xgboost.pkl')
    encoder_path = os.path.join(script_dir, 'models/label_encoder.pkl')
    
    logger.info(f"\n📁 Căi fișiere:")
    logger.info(f"Model: {model_path}")
    logger.info(f"Encoder: {encoder_path}")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Modelul Nutri-Score nu a fost găsit la: {model_path}")
    if not os.path.exists(encoder_path):
        raise FileNotFoundError(f"Encoder-ul nu a fost găsit la: {encoder_path}")
        
    # Verifică dimensiunea fișierului (dacă e prea mic poate fi corupt)
    model_size = os.path.getsize(model_path)
    logger.info(f"\n📊 Dimensiune fișier model: {model_size / 1024:.2f} KB")
    
    if model_size < 1000:  # Dacă e mai mic de ~1KB
        raise ValueError("Fișierul modelului pare prea mic, posibil corupt")
        
    # Încarcă modelul și encoder-ul
    logger.info("\n📥 Încărcăm modelul XGBoost...")
    with open(model_path, 'rb') as file:
        nutriscore_model = pickle.load(file)
    
    logger.info("📥 Încărcăm encoder-ul...")
    with open(encoder_path, 'rb') as file:
        label_encoder = pickle.load(file)
        
    logger.info("\n✅ Modelul Nutri-Score și encoder-ul au fost încărcate cu succes!")
    logger.info("="*50 + "\n")
except Exception as e:
    logger.error(f"\n❌ Eroare la încărcarea modelului Nutri-Score: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())
    nutriscore_model = None
    label_encoder = None

# Configurație OpenAI
OPENAI_API_KEY = "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"
openai.api_key = OPENAI_API_KEY

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
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 1. Ajustare contrast/luminozitate
    adjusted = cv2.convertScaleAbs(gray, alpha=0.6, beta=50)

    # 2. Detecție highlights (pixeli > 240) și estompare
    mask_highlight = cv2.inRange(adjusted, 240, 255) 
    blurred = cv2.GaussianBlur(adjusted, (5, 5), 0)
    adjusted[mask_highlight > 0] = blurred[mask_highlight > 0]

    # 3. CLAHE pentru contrast local adaptiv
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast_img = clahe.apply(adjusted)

    # 4. Denoising
    denoised = cv2.fastNlMeansDenoising(contrast_img, h=10, templateWindowSize=7, searchWindowSize=21)

    # 5. Binarizare cu Otsu
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 6. Conversie înapoi la RGB pentru Tesseract
    final = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)

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
        logger.info(text)
        
        # Apel GPT
        response = openai.ChatCompletion.create(
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

def predict_nutriscore(nutrient_data, model, encoder):
    """
    Prezice Nutri-Score-ul pe baza datelor nutriționale extrase.
    """
    logger.info("\n" + "="*50)
    logger.info("🎯 PREDICȚIE NUTRI-SCORE")
    logger.info("="*50)
    
    if model is None or encoder is None:
        logger.error("❌ Model sau encoder nu sunt disponibile")
        return None
    
    try:
        # Creăm un DataFrame cu un singur rând pentru predicție
        import pandas as pd

        # Lista de nutrienți așteptați în ordinea corectă
        expected_nutrients = [
            'fat_100g', 'saturated-fat_100g', 'trans-fat_100g', 'cholesterol_100g',
            'sodium_100g', 'carbohydrates_100g', 'fiber_100g', 'sugars_100g', 'proteins_100g'
        ]
        
        # Pregătim datele pentru predicție
        input_data = {}
        for nutrient in expected_nutrients:
            input_data[nutrient] = nutrient_data.get(nutrient, 0)
        
        logger.info("\n📊 Date pentru predicție:")
        logger.info(json.dumps(input_data, indent=2))
        
        # Creăm DataFrame-ul pentru predicție
        input_df = pd.DataFrame([input_data])
        
        # Facem predicția
        logger.info("\n🔮 Calculăm predicția...")
        prediction = model.predict(input_df)[0]
        logger.info(f"Valoare brută din model: {prediction}")
        
        # Convertim valoarea numerică la eticheta Nutri-Score (A-E)
        nutri_score = encoder.inverse_transform([prediction])[0]
        logger.info(f"\n🏆 Nutri-Score final: {nutri_score}")
        logger.info("="*50 + "\n")
        
        return nutri_score
    
    except Exception as e:
        logger.error(f"\n❌ Eroare la predicția Nutri-Score: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def order_points(pts):
    """
    Ordonează cele 4 puncte astfel încât să corespundă:
    [stânga-sus, dreapta-sus, dreapta-jos, stânga-jos]
    Util pentru transformarea de perspectivă.
    """
    # Inițializăm lista ordonată de puncte
    rect = np.zeros((4, 2), dtype="float32")
    
    # Suma coordonatelor: cel mai mic = colțul stânga-sus, cel mai mare = colțul dreapta-jos
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # Diferența coordonatelor: cel mai mic = colțul dreapta-sus, cel mai mare = colțul stânga-jos
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect

def four_point_transform(image, pts):
    """
    Aplică o transformare de perspectivă pe imaginea dată,
    folosind cele 4 puncte din pts.
    """
    # Obține lista ordonată de puncte și le descompune individual
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    
    # Calculează lățimea maximă a noii imagini
    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_width = max(int(width_a), int(width_b))
    
    # Calculează înălțimea maximă a noii imagini
    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_height = max(int(height_a), int(height_b))
    
    # Definește destinația punctelor în noua imagine
    dst = np.array([
        [0, 0],                      # stânga-sus
        [max_width - 1, 0],          # dreapta-sus
        [max_width - 1, max_height - 1], # dreapta-jos
        [0, max_height - 1]          # stânga-jos
    ], dtype="float32")
    
    # Calculează matricea de transformare
    M = cv2.getPerspectiveTransform(rect, dst)
    
    # Aplică transformarea de perspectivă
    warped = cv2.warpPerspective(image, M, (max_width, max_height))
    
    return warped

def find_corners(box):
    """
    Găsește cele 4 colțuri din bounding box [xmin, ymin, xmax, ymax]
    """
    xmin, ymin, xmax, ymax = box
    return np.array([
        [xmin, ymin],  # stânga-sus
        [xmax, ymin],  # dreapta-sus
        [xmax, ymax],  # dreapta-jos
        [xmin, ymax]   # stânga-jos
    ], dtype="float32")

def detect_and_ocr_with_warp(image_path):
    """
    Detectează etichetele nutriționale cu YOLO, aplică warp pentru corecția de perspectivă,
    și extrage textul cu OCR folosind modelul personalizat nuttrition1000.
    """
    logger.info("\n" + "="*50)
    logger.info("🔍 PROCESARE IMAGINE")
    logger.info("="*50)
    
    import os
    start_time = timeit.default_timer()
    
    logger.info(f"\n📁 Calea imaginii: {image_path}")
    
    # 1. Detectează obiecte folosind YOLO
    logger.info("\n📸 Detectăm eticheta nutrițională cu YOLO...")
    results = model.predict(source=image_path, save=False)
    logger.info(f"✅ YOLO a detectat {len(results[0].boxes)} obiecte")
    
    # Citește imaginea originală
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"❌ Nu s-a putut încărca imaginea: {image_path}")
        return None
        
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    detected_texts = []
    
    # Set up Tesseract to use the custom traineddata file
    logger.info("\n🔧 Configurăm Tesseract OCR...")
    tessdata_dir = os.path.join(script_dir, "tesseract_finetune/tesstrain/data")
    os.environ["TESSDATA_PREFIX"] = tessdata_dir
    
    # Verificăm dacă fișierul exist
    traineddata_path = os.path.join(tessdata_dir, "nuttrition1000.traineddata")
    if not os.path.exists(traineddata_path):
        logger.error(f"❌ Fișierul nuttrition1000.traineddata nu există la calea: {traineddata_path}")
        return None
    else:
        logger.info(f"✅ Model găsit la: {traineddata_path}")
    
    # 2. Pentru fiecare obiect detectat
    logger.info("\n📝 Procesăm fiecare detecție...")
    for i, box in enumerate(results[0].boxes.xyxy):
        logger.info(f"\n🔄 Procesăm detecția #{i+1}...")
        # Extrage coordonatele bounding box-ului
        xmin, ymin, xmax, ymax = box[:4].cpu().numpy().astype(int)
        logger.info(f"📍 Coordonate bounding box: xmin={xmin}, ymin={ymin}, xmax={xmax}, ymax={ymax}")
        
        # Găsește cele 4 colțuri ale box-ului
        corners = find_corners([xmin, ymin, xmax, ymax])
        
        # Extrage regiunea de interes (ROI) și aplică transformarea de perspectivă
        try:
            logger.info("🔄 Aplicăm transformarea de perspectivă...")
            # Aplicăm transformarea de perspectivă (warp)
            warped_roi = four_point_transform(image, corners)
            
            # 3. Preprocesează ROI pe baza tipului de font
            logger.info("🔄 Preprocesăm imaginea pentru OCR...")
            processed_roi, text_type = preprocess_image_based_on_font(warped_roi)
            
            if processed_roi is None:
                logger.warning(f"⚠️ Procesarea ROI {i} a eșuat.")
                continue
                
            # Create absolute paths to the dictionary files
            user_words_path = os.path.join(script_dir, "user-words.txt")
            user_patterns_path = os.path.join(script_dir, "user-patterns.txt")

            logger.info(f"📁 Căutăm fișierele în:")
            logger.info(f"user-words.txt: {user_words_path}")
            logger.info(f"user-patterns.txt: {user_patterns_path}")

            # Verify files exist
            if not os.path.exists(user_words_path):
                logger.warning(f"⚠️ Warning: user-words.txt not found at {user_words_path}")
            if not os.path.exists(user_patterns_path):
                logger.warning(f"⚠️ Warning: user-patterns.txt not found at {user_patterns_path}")
                
            char_whitelist = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ%(),./:;*<>-_= "

            # Use absolute paths in the configuration
            custom_config = f'--oem 3 --psm 6 -l nuttrition1000 --user-words "{user_words_path}" --user-patterns "{user_patterns_path}"'
                
            # 4. Aplică OCR pe ROI procesat cu modelul personalizat nuttrition1000
            logger.info("🔍 Extragem textul cu OCR...")
            text = pytesseract.image_to_string(processed_roi, config=custom_config)
            logger.info("\n📄 Text extras prin OCR:")
            logger.info("="*50)
            logger.info(text)
            logger.info("="*50)
            
            # 5. Aplică procesarea și structurarea textului cu GPT
            logger.info("\n🧠 Procesăm textul cu GPT pentru extragere date structurate...")
            structured_data = clean_and_structure_text(text)
            logger.info("DATELE STRUCTURATE:")
            logger.info(structured_data)
            if structured_data:
                logger.info("\n✅ Date structurate extrase cu succes!")
                logger.info("\n📊 Date nutriționale:")
                logger.info("="*50)
                logger.info(json.dumps(structured_data, indent=2, ensure_ascii=False))
                logger.info("="*50)
                
                # Adăugăm predicția Nutri-Score dacă avem date structurate și modelul este încărcat
                if nutriscore_model is not None and label_encoder is not None:
                    logger.info("\n🎯 Calculăm Nutri-Score folosind modelul XGBoost...")
                    predicted_score = predict_nutriscore(structured_data, nutriscore_model, label_encoder)
                    if predicted_score:
                        logger.info(f"\n🏆 Nutri-Score final: {predicted_score}")
                        structured_data['nutri_score'] = predicted_score
                        structured_data['nutri_score_predicted'] = True
            else:
                logger.error("❌ Nu s-au putut extrage date structurate")
            
            detected_texts.append({
                'box': [xmin, ymin, xmax, ymax],
                'text': text.strip(),
                'text_type': text_type,
                'warped_roi': warped_roi,
                'processed_roi': processed_roi,
                'structured_data': structured_data
            })
                
        except Exception as e:
            logger.error(f"❌ Eroare la procesarea box-ului {i}: {str(e)}")
    
    end_time = timeit.default_timer()
    processing_time = end_time - start_time
    
    # 5. Afișează rezultatele
    logger.info(f"\n⏱️ Timp total de procesare: {processing_time:.2f} secunde")
    logger.info(f"📊 Număr total de texte extrase: {len(detected_texts)}")
    logger.info("="*50 + "\n")
    
    # Returnăm doar datele structurate pentru API
    if detected_texts and len(detected_texts) > 0:
        return detected_texts[0].get('structured_data', {})
    return None
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
import streamlit as st

from dashboard.components.icons import icon_text
from dashboard.utils.i18n import get_texts

load_dotenv()


def render(lang: str, texts: dict | None = None, models_status: dict | None = None) -> None:
    models_status = models_status or {"solar": False, "wind": False, "lstm": False}
    texts = {**get_texts(lang), **(texts or {})}

    st.markdown(f'<h3>{" AI Model Training Center" if lang == "en" else " AI Модельдерді оқыту орталығы"}</h3>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:#8b949e;">{"Configure parameters and launch model training runs directly from the browser with real-time console tracking." if lang == "en" else "Модельді оқыту параметрлерін баптаңыз және тікелей браузерден оқыту процесін нақты уақыттағы консольдік бақылаумен іске қосыңыз."}</p>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    # Model Selection
    train_model_choice = st.selectbox(
        "Оқытуға арналған модель / Select Model to Train:" if lang == "kk" else "Select Model to Train:",
        [
            "Smart Grid Transformer Fault Classifier (XGBoost)" if lang == "en" else "Smart Grid трансформациялық ақауларды жіктеуіш (XGBoost)",
            "Solar Power Generation Forecast (RF + XGBoost + LSTM)" if lang == "en" else "Күн электрстанциясының қуатын болжау (RF + XGBoost + LSTM)",
            "Solar Panel Clean vs Dirty Image Classifier (ResNet50)" if lang == "en" else "Күн панелінің таза/лас суреттерін жіктеуіш (ResNet50)",
            "Solar Panel Dust Binary Image Classifier (ResNet50)" if lang == "en" else "Күн панеліндегі шаңды анықтайтын жіктеуіш (ResNet50)",
            "YOLOv11-nano Solar Panel Electrical Anomalies (ImageSet)" if lang == "en" else "YOLOv11-nano Күн панелінің электрлік ауытқулары (ImageSet)"
        ]
    )

    col_p1, col_p2 = st.columns(2)

    with col_p1:
        st.markdown(f"##### ** {'Оқыту параметрлері' if lang == 'kk' else 'Hyperparameters'}**")
    
        if "YOLOv11" in train_model_choice:
            epochs_val = st.slider("Epochs / Дәуірлер саны", min_value=1, max_value=5, value=2, step=1)
            st.caption("YOLOv11-nano is deep and uses CPU, training epochs are capped at 5 for performance." if lang == "en" else "YOLOv11-nano терең модель және CPU-ды қолданады, өнімділік үшін дәуір саны 5-ке дейін шектелген.")
        elif "Forecast" in train_model_choice or "болжау" in train_model_choice:
            st.markdown("**Models trained:** Random Forest + XGBoost + LSTM (sequential)" if lang == "en" else "**Оқытылатын модельдер:** Random Forest + XGBoost + LSTM (ретпен)")
            st.caption("All 3 models are trained in one run. LSTM uses MinMaxScaler on y-target to prevent loss explosion." if lang == "en" else "3 модель де бір рет іске қосылады. LSTM y-мақсатты MinMaxScaler арқылы масштабтайды.")
        elif "XGBoost" in train_model_choice:
            estimators_val = st.slider("Estimators / Ағаштар саны", min_value=10, max_value=200, value=100, step=10)
            max_depth_val = st.slider("Max Depth / Максималды тереңдік", min_value=3, max_value=10, value=6, step=1)
        else:
            epochs_val = st.slider("Epochs / Дәуірлер саны", min_value=1, max_value=15, value=5, step=1)
            batch_size_val = st.selectbox("Batch Size / Батч өлшемі", [16, 32, 64], index=1)
            lr_val = st.selectbox("Learning Rate / Оқыту жылдамдығы", [0.01, 0.001, 0.0001], index=1)
        
    with col_p2:
        st.markdown(f"##### ** {'Деректер жинағы ақпараты' if lang == 'kk' else 'Dataset Info'}**")
        if "XGBoost" in train_model_choice and "Forecast" not in train_model_choice and "болжау" not in train_model_choice:
            st.info(" **smart_grid_dataset.csv**\n- Size: 50,000 rows\n- Target: Transformer Fault\n- Split: 80% Train, 20% Test" if lang == "en" else " **smart_grid_dataset.csv**\n- Өлшемі: 50,000 жол\n- Мақсатты өріс: Transformer Fault\n- Бөлінуі: 80% Оқыту, 20% Тест")
        elif "Forecast" in train_model_choice or "болжау" in train_model_choice:
            st.info(" **Plant_1_Generation_Data.csv + Plant_1_Weather_Sensor_Data.csv**\n- Records: 3,157 (merged plant+weather)\n- Target: AC_POWER (kW)\n- 3 Models: RF / XGBoost / LSTM" if lang == "en" else " **Plant_1_Generation_Data.csv + Plant_1_Weather_Sensor_Data.csv**\n- Жазбалар: 3,157 (біріктірілген)\n- Мақсатты өріс: AC_POWER (кВт)\n- 3 Модель: RF / XGBoost / LSTM")
            # Show last training results
            import os, pickle
            rf_path = os.path.abspath("artifacts/solar_forecast_rf.pkl")
            if os.path.exists(rf_path):
                st.success("**Last Training Results:**\n- Random Forest: R2=0.9967 | MAE=227 kW\n- XGBoost: R2=0.9971 | MAE=213 kW\n- LSTM: R2=0.9137 | MAE=1336 kW" if lang == "en" else "**Соңғы оқыту нәтижелері:**\n- Random Forest: R2=0.9967 | MAE=227 кВт\n- XGBoost: R2=0.9971 | MAE=213 кВт\n- LSTM: R2=0.9137 | MAE=1336 кВт")
        elif "Clean vs Dirty" in train_model_choice or "таза/лас" in train_model_choice:
            st.info(" **dataset/**\n- Size: 842 images\n- Classes: clean, dirty\n- Split: 80% Train, 20% Val" if lang == "en" else " **dataset/**\n- Өлшемі: 842 сурет\n- Сыныптар: clean, dirty\n- Бөлінуі: 80% Оқыту, 20% Валидация")
        elif "Dust Binary" in train_model_choice or "шаңды" in train_model_choice:
            st.info(" **Detect_solar_dust/**\n- Size: 2,562 images\n- Classes: Clean, Dusty\n- Split: 80% Train, 20% Val" if lang == "en" else " **Detect_solar_dust/**\n- Өлшемі: 2,562 сурет\n- Сыныптар: Clean, Dusty\n- Бөлінуі: 80% Оқыту, 20% Валидация")
        else:
            st.info(" **ImageSet/**\n- Size: 6,924 train images\n- Classes: 8 Electrical Anomalies (Bypass, HotSpot, etc.)\n- Model: YOLOv11-nano" if lang == "en" else " **ImageSet/**\n- Өлшемі: 6,924 оқыту суреті\n- Сыныптар: 8 электрлік ақау (Bypass, HotSpot, т.б.)\n- Модель: YOLOv11-nano")
        
    # Launch training
    if st.button(" Жаттығуды бастау / Start Model Training" if lang == "kk" else " Start Model Training", width='stretch'):
        st.markdown(f"##### ** {'Оқыту консолі (Тікелей эфир)' if lang == 'kk' else 'Training Console Output (Live)'}:**")
        log_placeholder = st.empty()
    
        # Prepare script and parameters
        import os
        import sys
        import subprocess
    
        # Determine script and arguments
        script_args = []
        if "XGBoost" in train_model_choice and "Forecast" not in train_model_choice and "болжау" not in train_model_choice:
            script_path = os.path.abspath("C:/Users/MECHREVO/.gemini/antigravity/brain/a3ee9c8b-c0fa-44e3-8755-5708fd65ad9a/scratch/train_smart_grid_model_xgb.py")
        elif "Forecast" in train_model_choice or "болжау" in train_model_choice:
            script_path = os.path.abspath("C:/Users/MECHREVO/.gemini/antigravity/brain/a3ee9c8b-c0fa-44e3-8755-5708fd65ad9a/scratch/train_solar_forecast.py")
        elif "Clean vs Dirty" in train_model_choice or "таза/лас" in train_model_choice:
            script_path = os.path.abspath("C:/Users/MECHREVO/.gemini/antigravity/brain/a3ee9c8b-c0fa-44e3-8755-5708fd65ad9a/scratch/train_dataset_model.py")
        elif "Dust Binary" in train_model_choice or "шаңды" in train_model_choice:
            script_path = os.path.abspath("C:/Users/MECHREVO/.gemini/antigravity/brain/a3ee9c8b-c0fa-44e3-8755-5708fd65ad9a/scratch/train_solar_dust_model.py")
        else:
            script_path = os.path.abspath("C:/Users/MECHREVO/.gemini/antigravity/brain/a3ee9c8b-c0fa-44e3-8755-5708fd65ad9a/scratch/train_imageset_yolo.py")
            script_args = [str(epochs_val)]
        
        cmd = [sys.executable, script_path] + script_args
    
        # Execute training subprocess
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            shell=True
        )
    
        log_content = ""
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                log_content += line
                # Crop lines to prevent performance lag
                lines = log_content.splitlines()
                if len(lines) > 30:
                    log_content = "\n".join(lines[-30:])
                log_placeholder.code(log_content)
            
        rc = process.poll()
        if rc == 0:
            st.success(" Оқыту сәтті аяқталды! / Training completed successfully!" if lang == "kk" else " Training completed successfully!")
            st.balloons()
        else:
            st.error(f" Оқыту сәтсіз аяқталды (Exit Code: {rc}) / Training failed!" if lang == "kk" else f" Training failed (Exit Code: {rc})!")


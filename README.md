⚡ EcoPredict AI

An AI system that predicts and optimizes hybrid energy generation using solar and wind data.
The system integrates machine learning models, a FastAPI backend, and a Streamlit dashboard to provide energy predictions, optimization, and explanations.

⸻

🚀 Project Overview

Renewable energy systems often rely on multiple sources like solar and wind.
This project builds an AI-powered hybrid energy prediction platform that:
	•	Predicts solar power generation
	•	Predicts wind power generation
	•	Performs hybrid energy optimization
	•	Recommends the best energy source
	•	Provides AI explanation for decisions
	•	Displays results through an interactive dashboard

🧠 System Architecture
User Interface (Streamlit)
        ↓
FastAPI Backend API
        ↓
Machine Learning Models
        ↓
Hybrid Optimization Engine
        ↓
AI Advisor Explanation

This architecture follows real production ML system design where frontend and ML inference are separated.


🛠 Tech Stack

Programming
	•	Python

Machine Learning
	•	Scikit-learn
	•	XGBoost
	•	TensorFlow / LSTM

Backend
	•	FastAPI
	•	Uvicorn

Frontend
	•	Streamlit
	•	Plotly

Utilities
	•	NumPy
	•	Pandas
	•	Joblib

⸻

📂 Project Structure

EcoPredict AI
│
├── api
│   ├── main.py
│   └── routes.py
│
├── dashboard
│   └── app.py
│
├── src
│   ├── data_pipeline
│   ├── models
│   ├── optimization
│   ├── llm_agent
│   ├── rag
│   └── utils
│
├── configs
│   ├── data_config.yaml
│   └── model_config.yaml
│
├── artifacts
│   ├── solar_model.pkl
│   └── wind_model.pkl
│
├── data
│
├── requirements.txt
└── README.md

⚙️ Installation

Clone the repository
pip install -r requirements.txt

▶️ Running the Project

1️⃣ Start Backend API
uvicorn api.main:app --reload

API docs will be available at:
http://127.0.0.1:8000/docs

2️⃣ Start Dashboard
streamlit run dashboard/app.py

Dashboard will open at:
http://localhost:8501

📊 Dashboard Features
	•	Solar energy prediction
	•	Wind energy prediction
	•	Hybrid energy optimization
	•	Recommended energy source
	•	Energy comparison graph
	•	AI explanation for energy selection



📈 Example Output
Solar Power: 1255 kW
Wind Power: 651 kW
Total Energy: 1906 kW
Recommended Source: Solar

🔮 Future Improvements

Planned upgrades for the system:
	•	Real-time weather API integration
	•	24-hour energy forecasting
	•	Battery storage optimization
	•	AI chatbot energy advisor
	•	Cloud deployment (AWS / Render)



🎯 Use Cases
	•	Renewable energy management
	•	Smart grid systems
	•	Energy planning & optimization
	•	AI-assisted renewable energy decisions




⭐ If you like this project

Give it a star on GitHub ⭐
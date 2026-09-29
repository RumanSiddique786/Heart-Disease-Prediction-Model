import streamlit as st
import pandas as pd
import numpy as np
import joblib
from tensorflow.keras.models import load_model
from datetime import datetime
import os
from io import BytesIO

# For PDF Report
try:
    from cardioguard_pdf import create_cardioguard_report
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# ====================== Page Configuration ======================
st.set_page_config(
    page_title="CardioGuard - Heart Disease Predictor",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {padding: 2rem;}
    .stButton>button {width: 100%; height: 3rem; font-size: 1.1rem;}
    .result-card {padding: 25px; border-radius: 12px; margin: 15px 0;}
    </style>
""", unsafe_allow_html=True)

st.title("❤️ CardioGuard")
st.markdown("### **AI-Powered Heart Disease Prediction System**")
st.caption("Final Year Major Project | Stacking Classifier + Neural Network")

# ====================== Load Models ======================
@st.cache_resource
def load_models():
    model = joblib.load('heart_model.pkl')
    scaler = joblib.load('rfe_scaler.pkl')
    nn_model = load_model('heart_nn_model.keras')
    
    with open('selected_features.txt', 'r') as f:
        selected_features = [feat.strip() for feat in f.read().split(',')]
    
    return model, scaler, nn_model, selected_features

try:
    model, scaler, nn_model, selected_features = load_models()
except Exception as e:
    st.error(f"❌ Error loading models: {e}")
    st.error("Please run train_model.py first!")
    st.stop()

original_columns = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 
                    'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal']

# ====================== Reset Function ======================
def reset_inputs():
    st.session_state["patient_name"] = ""
    st.session_state["age"] = 55
    st.session_state["sex"] = "Male"
    st.session_state["cp"] = "Typical Angina (1)"
    st.session_state["trestbps"] = 130
    st.session_state["chol"] = 240
    st.session_state["fbs"] = "No"
    st.session_state["restecg"] = "Normal (0)"
    st.session_state["thalach"] = 150
    st.session_state["thal"] = "Normal (3)"
    st.session_state["exang"] = "No"
    st.session_state["oldpeak"] = 1.0
    st.session_state["slope"] = "Upsloping (1)"
    st.session_state["ca"] = "0"

if "age" not in st.session_state:
    st.session_state.update({
        "patient_name": "",
        "age": 55,
        "sex": "Male",
        "cp": "Typical Angina (1)",
        "trestbps": 130,
        "chol": 240,
        "fbs": "No",
        "restecg": "Normal (0)",
        "thalach": 150,
        "thal": "Normal (3)",
        "exang": "No",
        "oldpeak": 1.0,
        "slope": "Upsloping (1)",
        "ca": "0"
    })
# ====================== Input Form ======================
col1, col2 = st.columns(2)

patient_name = st.text_input("Patient Name (for Report)", placeholder="Enter patient full name here", key="patient_name")
col1, col2, col3 = st.columns(3)

with col1:
    age = st.slider("Age (years)", 20, 80, key="age")
    sex = st.selectbox("Gender", ["Male", "Female"], key="sex")
    cp = st.selectbox("Chest Pain Type", 
                      ["Typical Angina (1)", "Atypical Angina (2)", 
                       "Non-anginal Pain (3)", "Asymptomatic (4)"], key="cp")
    trestbps = st.slider("Resting Blood Pressure (mm Hg)", 90, 200, key="trestbps")

with col2:
    chol = st.slider("Serum Cholesterol (mg/dl)", 100, 400, key="chol")
    fbs = st.selectbox("Fasting Blood Sugar > 120 mg/dl", ["No", "Yes"], key="fbs")
    restecg = st.selectbox("Resting ECG Results", 
                           ["Normal (0)", "ST-T Abnormality (1)", "LV Hypertrophy (2)"], key="restecg")
    thalach = st.slider("Maximum Heart Rate Achieved", 70, 200, key="thalach")
    thal = st.selectbox("Thalassemia",
                        ["Normal (3)", "Fixed Defect (6)", "Reversible Defect (7)"], key="thal")

with col3:
    exang = st.selectbox("Exercise Induced Angina", ["No", "Yes"], key="exang")
    oldpeak = st.slider("ST Depression (mm)", 0.0, 6.0, key="oldpeak")
    slope = st.selectbox("Slope of ST Segment",
                         ["Upsloping (1)", "Flat (2)", "Downsloping (3)"], key="slope")
    ca = st.selectbox("Major Vessels (0-3)", ["0", "1", "2", "3"], key="ca")
    
# Prepare input data
input_data = [
    age, 1 if sex == "Male" else 0,
    int(cp.split("(")[1].strip(")")),
    trestbps, chol,
    1 if fbs == "Yes" else 0,
    int(restecg.split("(")[1].strip(")")),
    thalach,
    1 if exang == "Yes" else 0,
    oldpeak,
    int(slope.split("(")[1].strip(")")),
    int(ca),
    int(thal.split("(")[1].strip(")"))
]

# ====================== Prediction Functions ======================
def predict_with_stacking(new_data):
    new_data = np.array(new_data).reshape(1, -1)
    feature_indices = [list(original_columns).index(feat) for feat in selected_features]
    new_data_rfe = new_data[:, feature_indices]
    new_data_df = pd.DataFrame(new_data_rfe, columns=selected_features)
    new_data_scaled = scaler.transform(new_data_df)
    
    pred = model.predict(new_data_scaled)
    prob = model.predict_proba(new_data_scaled)[0][1]
    return "High Risk" if pred[0] == 1 else "Low Risk", round(float(prob) * 100, 2)

def predict_with_nn(new_data):
    new_data = np.array(new_data).reshape(1, -1)
    feature_indices = [list(original_columns).index(feat) for feat in selected_features]
    new_data_rfe = new_data[:, feature_indices]
    new_data_df = pd.DataFrame(new_data_rfe, columns=selected_features)
    new_data_scaled = scaler.transform(new_data_df)
    
    prob = nn_model.predict(new_data_scaled, verbose=0)[0][0]
    return "High Risk" if prob > 0.5 else "Low Risk", round(float(prob) * 100, 2)

# ====================== Result Display ======================
def show_result(risk_level, probability, model_name, patient_name="[Patient Name]"):
    probability = float(probability)
    
    if risk_level == "High Risk":
        st.markdown(f"""
        <div class="result-card" style="background-color:#ffebee; border-left:6px solid #d32f2f;">
            <h2 style="color:#d32f2f;">⚠️ HIGH RISK - Heart Disease Likely</h2>
            <h1 style="color:#d32f2f;">{probability}%</h1>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="result-card" style="background-color:#e8f5e9; border-left:6px solid #388e3c;">
            <h2 style="color:#388e3c;">✅ LOW RISK - No Heart Disease Detected</h2>
            <h1 style="color:#388e3c;">{probability}%</h1>
        </div>
        """, unsafe_allow_html=True)

    st.metric("Model Used", model_name)
    st.progress(probability / 100)

    report_txt = f"""CardioGuard - Heart Disease Prediction Report
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Model Used: {model_name}
Risk Level: {risk_level}
Probability: {probability}%

Patient Details:
Patient Name: {patient_name}
Age: {age} years | Gender: {sex}
Chest Pain: {cp} | Resting BP: {trestbps} mm Hg
Cholesterol: {chol} mg/dl | Max Heart Rate: {thalach}
"""

    st.download_button("📥 Download TXT Report", report_txt,
                       f"CardioGuard_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt", "text/plain")

    if PDF_AVAILABLE:
        pdf_buffer = create_cardioguard_report(
            age=age, sex=sex, cp=cp, trestbps=trestbps,
            chol=chol, thalach=thalach,
            exang=1 if exang=="Yes" else 0,
            oldpeak=oldpeak, slope=slope, ca=ca, thal=thal,
            fbs=1 if fbs=="Yes" else 0, restecg=restecg,
            risk_level=risk_level, probability=probability,
            model_name=model_name,
            logo_path="logo_clean.png",
            patient_name=patient_name if patient_name else "[Patient Name]"
        )
        st.download_button("📄 Download CardioGuard AI Report",
                           pdf_buffer.getvalue(),
                           f"CardioGuard_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                           "application/pdf")
    

# ====================== Tabs ======================
tab1, tab2 = st.tabs(["🩺 Make Prediction", "📊 Model Performance"])

with tab1:
    col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 1])
    
    with col_btn1:
        if st.button("🔍 Predict using Stacking Model", type="primary"):
            with st.spinner("Analyzing with Stacking Classifier..."):
                result, probability = predict_with_stacking(input_data)
            show_result(result, probability, "Stacking Classifier (RF + SVM + XGBoost)", patient_name)

    with col_btn2:
        if st.button("🧠 Predict using Neural Network", type="secondary"):
            with st.spinner("Analyzing with Neural Network..."):
                result, probability = predict_with_nn(input_data)
            show_result(result, probability, "Neural Network", patient_name)

       # Reset defaults
# if "reset_defaults" not in st.session_state:
#     st.session_state["reset_defaults"] = False
    
with col_btn3:
    st.button("🔄 Reset", on_click=reset_inputs)

with tab2:
    st.subheader("Model Performance & Explainability")
    st.info("These visualizations were generated during training using SMOTE, RFE, and SHAP analysis.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if os.path.exists("confusion_matrix.png"):
            st.image("confusion_matrix.png", caption="Confusion Matrix")
        else:
            st.warning("Run train_model.py first")
    
    with col_b:
        if os.path.exists("shap_summary.png"):
            st.image("shap_summary.png", caption="SHAP Feature Importance")
        else:
            st.warning("Run train_model.py first")

    if os.path.exists("roc_curve.png"):
        st.image("roc_curve.png", caption="ROC Curve - Stacking Classifier")
    else:
        st.warning("Run train_model.py first")

st.markdown("---")
st.caption("Made with ❤️ CardioGuard AI System | Machine Learning Powered Platform | Developed by Ruman Tanveer as a B.Tech Final Year Project")
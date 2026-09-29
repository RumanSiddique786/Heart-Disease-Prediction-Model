import os
import warnings
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import shap

# ====================== Suppress Warnings ======================
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'          # Suppress GPU/CUDA warnings

warnings.filterwarnings("ignore")                  # Suppress ALL warnings globally

# Specific suppressions for known noisy libraries
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
warnings.filterwarnings("ignore", category=ImportWarning)

# Suppress XGBoost, sklearn, SHAP, TensorFlow specific messages
warnings.filterwarnings("ignore", module="xgboost")
warnings.filterwarnings("ignore", module="sklearn")
warnings.filterwarnings("ignore", module="shap")
warnings.filterwarnings("ignore", module="tensorflow")
warnings.filterwarnings("ignore", module="keras")

# Suppress SMOTE / imbalanced-learn warnings
warnings.filterwarnings("ignore", module="imblearn")

# Suppress scikeras warnings
warnings.filterwarnings("ignore", module="scikeras")

import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('absl').setLevel(logging.ERROR)
logging.getLogger('xgboost').setLevel(logging.ERROR)
logging.getLogger('shap').setLevel(logging.ERROR)

# ====================== IMPORTS (This was missing!) ======================
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.feature_selection import RFE
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from imblearn.over_sampling import SMOTE
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, Dense, Dropout
from scikeras.wrappers import KerasClassifier
from xgboost import XGBClassifier

print("🚀 Starting Heart Disease Model Training...\n")

# ====================== Load Dataset ======================
dataset_path = 'heart.csv'

if not os.path.exists(dataset_path):
    raise FileNotFoundError(f"❌ '{dataset_path}' not found! Place heart.csv in this folder.")

df = pd.read_csv(dataset_path, header=0)
print(f"✅ Dataset loaded! Shape: {df.shape}")

df.columns = df.columns.str.strip()

if 'diagnosis' in df.columns:
    df = df.rename(columns={'diagnosis': 'target'})
    print("Renamed 'diagnosis' → 'target'")

df = df.replace('?', np.nan)
df = df.astype(float)
df = df.dropna()
df['target'] = df['target'].apply(lambda x: 1 if x > 0 else 0)

print(f"✅ Final cleaned dataset shape: {df.shape}")

# ====================== Preprocessing ======================
X = df.drop('target', axis=1)
y = df['target']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
y_test = np.array(y_test).flatten()

# SMOTE
smote = SMOTE(random_state=42)
X_train, y_train = smote.fit_resample(X_train, y_train)

# RFE Feature Selection
rfe_selector = RFE(estimator=RandomForestClassifier(n_estimators=100, random_state=42), 
                   n_features_to_select=8)
rfe_selector.fit(X_train, y_train)

selected_features = X.columns[rfe_selector.support_].tolist()
print("Selected features:", selected_features)

X_train_rfe = X_train[selected_features]
X_test_rfe = X_test[selected_features]

with open('selected_features.txt', 'w') as f:
    f.write(','.join(selected_features))

# Scaling
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_rfe)
X_test_scaled = scaler.transform(X_test_rfe)

joblib.dump(scaler, 'rfe_scaler.pkl')
joblib.dump(rfe_selector, 'rfe_selector.pkl')

# ====================== Anomaly Detection ======================
from sklearn.ensemble import IsolationForest

iso_forest = IsolationForest(contamination=0.05, random_state=42)
anomaly_labels = iso_forest.fit_predict(X_train_scaled)
anomaly_count = (anomaly_labels == -1).sum()
print(f"Anomalies detected in training data: {anomaly_count}")

X_train_scaled = X_train_scaled[anomaly_labels == 1]
y_train = np.array(y_train.values[anomaly_labels == 1]).flatten()
print(f"Training data shape after anomaly removal: {X_train_scaled.shape}")

# ====================== Stacking Model ======================
stacking = StackingClassifier(
    estimators=[
        ('rf', RandomForestClassifier(random_state=42)),
        ('svm', SVC(probability=True, random_state=42)),
        ('xgb', XGBClassifier(eval_metric='logloss', random_state=42))
    ],
    final_estimator=LogisticRegression()
)

param_grid = {
    'rf__n_estimators': [50, 100],
    'rf__max_depth': [None, 10],
    'svm__C': [0.1, 1.0]
}

grid_search = GridSearchCV(stacking, param_grid, cv=3, scoring='accuracy', n_jobs=-1)
grid_search.fit(X_train_scaled, y_train)

model = grid_search.best_estimator_
print(f"Best Hyperparameters: {grid_search.best_params_}")
print(f"Stacking Best CV Accuracy: {grid_search.best_score_:.4f}")

# ====================== Neural Network ======================
def create_nn_model():
    model = Sequential([
        Input(shape=(len(selected_features),)),
        Dense(64, activation='relu'),
        Dropout(0.2),
        Dense(32, activation='relu'),
        Dropout(0.2),
        Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

nn_model = create_nn_model()
nn_model.fit(X_train_scaled, y_train, epochs=50, batch_size=16, validation_split=0.2, verbose=0)

nn_loss, nn_accuracy = nn_model.evaluate(X_test_scaled, y_test, verbose=0)
print(f"Neural Network Accuracy: {nn_accuracy * 100:.2f}%")
nn_model.save('heart_nn_model.keras')

# ====================== Evaluation ======================
y_pred = model.predict(X_test_scaled)
print(f"Stacking Model Test Accuracy: {accuracy_score(y_test, y_pred)*100:.2f}%")
print(classification_report(y_test, y_pred))

# ROC-AUC Score
from sklearn.metrics import roc_auc_score, roc_curve

y_prob = model.predict_proba(X_test_scaled)[:, 1]
roc_auc = roc_auc_score(y_test, y_prob)
print(f"ROC-AUC Score: {roc_auc:.4f}")

# ROC Curve Plot
fpr, tpr, _ = roc_curve(y_test, y_prob)
plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, color='blue', label=f'ROC Curve (AUC = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='gray', linestyle='--', label='Random Classifier')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve - Stacking Classifier')
plt.legend()
plt.savefig('roc_curve.png')
plt.close()
print("✅ roc_curve.png saved")

# Cross Validation
print("\n--- Cross Validation ---")
cv_scores_stacking = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='accuracy')
print(f"Stacking CV Mean: {cv_scores_stacking.mean():.4f}")

try:
    nn_classifier = KerasClassifier(model=create_nn_model, epochs=25, batch_size=16, verbose=0, random_state=42)
    cv_scores_nn = cross_val_score(nn_classifier, X_train_scaled, y_train, cv=3, scoring='accuracy')
    print(f"Neural Network CV Mean: {cv_scores_nn.mean():.4f}")
except Exception as e:
    print(f"NN CV Warning: {e}")

# ====================== Visualizations for Streamlit ======================
print("\nGenerating plots for Streamlit...")

# Confusion Matrix
plt.figure(figsize=(8, 6))
sns.heatmap(confusion_matrix(y_test, y_pred), annot=True, fmt='d', cmap='Blues')
plt.title('Confusion Matrix - Stacking Classifier')
plt.savefig('confusion_matrix.png')
plt.close()
print("✅ confusion_matrix.png saved")

# SHAP Summary Plot
print("Generating SHAP plot...")
rf_model = model.named_estimators_['rf']
explainer = shap.TreeExplainer(rf_model)
shap_values = explainer.shap_values(X_test_scaled)

plt.figure(figsize=(10, 6))
shap.summary_plot(shap_values, X_test_scaled, feature_names=selected_features, show=False)
plt.title('SHAP Feature Importance')
plt.savefig('shap_summary.png')
plt.close()
print("✅ shap_summary.png saved")

# ====================== Prediction Function ======================
def predict_heart_disease(new_data):
    try:
        new_data = np.array(new_data).reshape(1, -1)
        with open('selected_features.txt', 'r') as f:
            selected_features = [feat.strip() for feat in f.read().split(',')]
        
        feature_indices = [list(X.columns).index(feat) for feat in selected_features]
        new_data_rfe = new_data[:, feature_indices]
        
        new_data_df = pd.DataFrame(new_data_rfe, columns=selected_features)
        new_data_scaled = scaler.transform(new_data_df)
        
        pred = model.predict(new_data_scaled)
        prob = model.predict_proba(new_data_scaled)[0][1]
        
        result = "❤️  Heart Disease Likely" if pred[0] == 1 else "✅ No Heart Disease"
        return result, round(prob * 100, 2)
        
    except Exception as e:
        return f"Error: {str(e)}", 0.0

# Example Prediction

# sample_data = [63, 1, 3, 145, 233, 1, 0, 150, 0, 2.3, 0, 0, 1] # Low Risk
# sample_data = [67, 1, 4, 160, 286, 0, 2, 108, 1, 1.5, 2, 3, 3] # Moderate
sample_data = [70, 1, 4, 178, 320, 1, 2, 95, 1, 3.5, 3, 3, 7] # High risk
result, prob = predict_heart_disease(sample_data)
print(f"\nSample Prediction: {result} (Confidence: {prob}%)")

# ====================== Save Final Model ======================
joblib.dump(model, 'heart_model.pkl')
print("\n✅ All models saved successfully!")
print("\n🎉 Training Completed! Now run: streamlit run app.py")
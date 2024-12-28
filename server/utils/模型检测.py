import joblib

try:
    model = joblib.load('svm_rbf_model.pkl')
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")

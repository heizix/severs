import os
import joblib
from androguard.core import apk
import pandas as pd
from flask import jsonify

# 加载训练好的 SVM 模型（使用 joblib）
def load_model(model_file):
    try:
        model_path = os.path.join(os.path.dirname(__file__), model_file)
        model = joblib.load(model_path)  # 使用 joblib 加载模型
        return model
    except Exception as e:
        print(f"Error loading model from {model_file}: {e}")
        raise

# 从 feature.csv 中读取特征名称
def load_features_from_csv(feature_csv):
    try:
        feature_csv_path = os.path.join(os.path.dirname(__file__), feature_csv)
        with open(feature_csv_path, "r") as f:
            selected_features = [line.strip() for line in f.readlines()]
        return selected_features
    except Exception as e:
        print(f"Error loading features from {feature_csv}: {e}")
        raise

# 特征提取函数
def extract_apk_features(apk_file, selected_features):
    try:
        app = apk.APK(apk_file)
        print(f"Processing {apk_file}...")

        permissions = app.get_permissions()
        features = {}

        # 根据 selected_features 提取特征
        for feature in selected_features:
            if feature in permissions:
                features[feature] = 1  # 如果特征在权限列表中，则标记为1
            else:
                features[feature] = 0  # 如果特征不在权限列表中，则标记为0

        return features
    except Exception as e:
        print(f"Error processing {apk_file}: {e}")
        return None

# 分析 APK 文件并进行预测
def analyze_apk(filepath):
    try:
        # 读取特征名称
        selected_features = load_features_from_csv("feature.csv")

        # 加载训练好的 SVM 模型
        model = load_model("svm_rbf_model.pkl")

        # 提取 APK 文件的特征
        features = extract_apk_features(filepath, selected_features)
        if features:
            # 将提取到的特征转换为模型需要的格式
            feature_vector = [features.get(feature, 0) for feature in selected_features]

            # 进行预测
            prediction = model.predict([feature_vector])[0]

            # 将预测结果转换为Python原生类型，避免无法序列化的情况
            prediction = int(prediction)  # 将int64转换为int

            return {
                "apk_file": filepath,
                "prediction": prediction
            }
        else:
            raise Exception("Failed to extract features from APK.")
    except Exception as e:
        raise Exception(f"Error during APK analysis: {str(e)}")

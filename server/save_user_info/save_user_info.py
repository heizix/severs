import os
import json
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

# 定义 Blueprint
save_user_info_bp = Blueprint('save_user_info', __name__)

# 配置路径
UPLOAD_FOLDER = 'server/uploads'
AVATAR_FOLDER = os.path.join(UPLOAD_FOLDER, 'avatars')
USER_DATA_FILE = os.path.join(UPLOAD_FOLDER, 'user', 'user_data.json')
os.makedirs(AVATAR_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)

# 加载用户数据
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# 保存用户数据
def save_user_data(data):
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# 路由：上传头像
@save_user_info_bp.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    if 'file' not in request.files or 'username' not in request.form:
        return jsonify({"error": "No file or username provided"}), 400

    file = request.files['file']
    username = request.form['username']
    filename = secure_filename(f"{username}.jpg")
    filepath = os.path.join(AVATAR_FOLDER, filename)

    # 删除旧头像（如果存在）
    if os.path.exists(filepath):
        os.remove(filepath)

    # 保存新头像
    file.save(filepath)

    # 更新用户数据
    users = load_user_data()
    if username in users:
        users[username]['avatar'] = filepath
        save_user_data(users)
        return jsonify({"status": "success", "message": "Avatar uploaded successfully", "avatar": filepath}), 200
    else:
        return jsonify({"error": "User not found"}), 404

# 路由：更新昵称
@save_user_info_bp.route('/update_nickname', methods=['POST'])
def update_nickname():
    data = request.json
    username = data.get('username')
    new_nickname = data.get('nickname')

    if not username or not new_nickname:
        return jsonify({"error": "Username and nickname are required"}), 400

    # 更新用户数据
    users = load_user_data()
    if username in users:
        users[username]['nickname'] = new_nickname
        save_user_data(users)
        return jsonify({"status": "success", "message": "Nickname updated successfully"}), 200
    else:
        return jsonify({"error": "User not found"}), 404

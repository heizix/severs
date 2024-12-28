import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from loguru import logger
from register.register_handler import register_user
from utils.apk_analyzer import analyze_apk
from login.login_handler import authenticate_user

# 设置 androguard 日志级别
import logging
logging.getLogger("androguard").setLevel(logging.ERROR)

# 初始化 Flask 应用
app = Flask(__name__, static_folder='static')  # 指定静态文件夹
CORS(app)

# 配置上传目录和用户数据路径
UPLOAD_FOLDER = 'server/uploads'
USER_FOLDER = os.path.join(UPLOAD_FOLDER, 'user')
AVATAR_FOLDER = os.path.join(UPLOAD_FOLDER, 'avatars')
HISTORY_FOLDER = os.path.join(UPLOAD_FOLDER, 'history')
USER_DATA_FILE = os.path.join(USER_FOLDER, 'user_data.json')
os.makedirs(USER_FOLDER, exist_ok=True)
os.makedirs(AVATAR_FOLDER, exist_ok=True)
os.makedirs(HISTORY_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 配置日志
logger.remove()  # 移除默认日志
logger.add("server.log", rotation="1 MB", level="INFO")  # 保留 INFO 级别以上日志

# 路由：根路径，返回静态页面
@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

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

# 保存查询历史记录
def save_user_history(username, record):
    history_file = os.path.join(HISTORY_FOLDER, f"{username}_history.json")
    history = []
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    history.append(record)
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4)

# 路由：注册用户
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not password or not email:
        logger.error("Missing required fields for registration")
        return jsonify({"error": "All fields are required"}), 400

    users = load_user_data()
    if username in users:
        logger.error(f"Username already exists: {username}")
        return jsonify({"error": "Username already exists"}), 400

    # 默认昵称为 user123，头像为空
    users[username] = {"password": password, "email": email, "nickname": "user123", "avatar": None}
    save_user_data(users)

    logger.info(f"User registered successfully: {username}")
    return jsonify({"status": "success", "message": "User registered successfully"}), 201

# 路由：登录用户
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        logger.error("Username and password are required for login")
        return jsonify({"error": "Username and password are required"}), 400

    is_authenticated, message = authenticate_user(username, password, USER_DATA_FILE)

    if is_authenticated:
        users = load_user_data()
        user_data = users.get(username, {})
        nickname = user_data.get("nickname", "user123")
        avatar = user_data.get("avatar", None)

        # 将头像路径标准化为 URL 格式
        if avatar:
            avatar = avatar.replace('\\', '/')

        logger.info(f"User logged in successfully: {username}, Nickname: {nickname}, Avatar: {avatar}")

        return jsonify({"status": "success", "nickname": nickname, "avatar": avatar}), 200
    else:
        logger.warning(f"Login failed for user: {username}")
        return jsonify({"error": message}), 401

# 路由：上传文件并分析
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            logger.error("No file provided for upload")
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        username = request.form.get('username')  # 可选参数
        if file.filename == '':
            logger.error("No file selected for upload")
            return jsonify({"error": "No file selected"}), 400

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        logger.info(f"File uploaded successfully: {filepath}")

        # 调用分析功能
        analysis_result = analyze_apk(filepath)

        # 保存查询历史
        if username:
            record = {"apk_file": file.filename, "prediction": analysis_result.get('prediction', 'Unknown')}
            save_user_history(username, record)

        return jsonify({"apk_file": file.filename, "prediction": analysis_result.get('prediction', 'Unknown')}), 200
    except Exception as e:
        logger.error(f"Error during file upload: {str(e)}")
        return jsonify({"error": "File upload failed"}), 500

# 路由：获取用户信息
@app.route('/user/profile', methods=['GET'])
def get_user_profile():
    username = request.args.get('username')
    if not username:
        logger.error("Username is required for fetching profile")
        return jsonify({"error": "Username is required"}), 400

    users = load_user_data()
    user_data = users.get(username)

    if user_data:
        avatar_url = user_data.get("avatar", None)
        if avatar_url:
            avatar_url = avatar_url.replace('\\', '/')

        logger.info(f"Profile fetched for user: {username}")
        return jsonify({
            "status": "success",
            "nickname": user_data.get("nickname", "user123"),
            "avatar_url": avatar_url
        }), 200

    logger.error(f"User not found: {username}")
    return jsonify({"error": "User not found"}), 404

# 路由：上传头像
@app.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    if 'file' not in request.files or 'username' not in request.form:
        logger.error("No file or username provided for avatar upload")
        return jsonify({"error": "No file or username provided"}), 400

    file = request.files['file']
    username = request.form['username']
    filepath = os.path.join(AVATAR_FOLDER, f"{username}.jpg")

    # 删除旧头像
    if os.path.exists(filepath):
        os.remove(filepath)

    file.save(filepath)

    users = load_user_data()
    if username in users:
        relative_path = os.path.relpath(filepath, start=os.getcwd())
        users[username]['avatar'] = relative_path
        save_user_data(users)

        avatar_url = relative_path.replace('\\', '/')
        logger.info(f"Avatar uploaded for user: {username}, Saved at: {avatar_url}")

        return jsonify({"status": "success", "message": "Avatar uploaded successfully", "avatar_url": avatar_url}), 200

    logger.error(f"User not found for avatar upload: {username}")
    return jsonify({"error": "User not found"}), 404

# 路由：更新用户昵称
@app.route('/update_nickname', methods=['POST'])
def update_nickname():
    data = request.json
    username = data.get('username')
    new_nickname = data.get('nickname')

    if not username or not new_nickname:
        logger.error("Username and nickname are required for updating nickname")
        return jsonify({"error": "Username and nickname are required"}), 400

    users = load_user_data()
    if username in users:
        users[username]['nickname'] = new_nickname
        save_user_data(users)
        logger.info(f"Nickname updated for user: {username} to {new_nickname}")
        return jsonify({"status": "success", "message": "Nickname updated successfully"}), 200

    logger.error(f"User not found: {username}")
    return jsonify({"error": "User not found"}), 404


# 路由：获取用户历史记录
@app.route('/get_history/<username>', methods=['GET'])
def get_history(username):
    history_file = os.path.join(HISTORY_FOLDER, f"{username}_history.json")
    if not os.path.exists(history_file):
        logger.warning(f"No history found for user: {username}")
        return jsonify([]), 404

    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        logger.info(f"History retrieved for user: {username}")
        return jsonify(history), 200
    except Exception as e:
        logger.error(f"Error retrieving history for user {username}: {str(e)}")
        return jsonify({"error": "Failed to retrieve history"}), 500


# 路由：Ping，用于测试服务是否正常运行
@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "success", "message": "pong"}), 200

# 启动 Flask 应用
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

import json
import os

def authenticate_user(username, password, user_data_file):
    """
    验证用户登录。
    :param username: 用户名
    :param password: 密码
    :param user_data_file: 用户数据文件路径
    :return: 如果验证成功返回 True，否则返回 False
    """
    print(f"Authenticating user: {username}")
    print(f"Using USER_DATA_FILE: {user_data_file}")

    if not os.path.exists(user_data_file):
        print("User data file does not exist")
        return False, "User data file does not exist"

    with open(user_data_file, 'r', encoding='utf-8') as f:
        try:
            users = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return False, "Invalid user data format"

    print(f"Loaded users: {users}")
    user = users.get(username)
    if user:
        print(f"User found: {user}")
        if user.get('password') == password:
            return True, "Authentication successful"
        else:
            print(f"Password mismatch for user: {username}")
    else:
        print(f"User not found: {username}")
    return False, "Invalid username or password"

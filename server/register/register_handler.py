import os
import json

USER_DATA_FILE = 'uploads/user_data.json'

def register_user(username, password, email):
    if not username or not password or not email:
        return {"status": "error", "message": "All fields are required"}

    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
        if username in users:
            return {"status": "error", "message": "User already exists"}
    else:
        users = {}

    users[username] = {"password": password, "email": email}
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)
    return {"status": "success", "message": "User registered successfully"}

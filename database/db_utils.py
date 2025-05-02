from pymongo import MongoClient
import bcrypt
from utils.image_utils import delete_profile_image

client = MongoClient("mongodb://localhost:27017/")
db = client["user_db"]
collection = db["users"]

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode("utf-8"), hashed)

def add_user(username, full_name, age, city, password, role="user", profile_image=None):
    hashed_pw = hash_password(password)
    user = {
        "username": username,
        "full_name": full_name,
        "age": age,
        "city": city,
        "password": hashed_pw,
        "role": role
    }
    if profile_image:
        user["profile_image"] = profile_image
    collection.insert_one(user)

def get_all_users():
    return collection.find()

def find_user(username):
    return collection.find_one({"username": username})

def login_user(username, input_password):
    user = find_user(username)
    if user and verify_password(input_password, user["password"]):
        return user
    return None

def get_user_role(username):
    user = collection.find_one({"username": username})
    return user.get("role", "user") if user else "user"

def delete_user(username):
    user = collection.find_one({"username": username})
    if user and "profile_image" in user:
        delete_profile_image(user["profile_image"])
    return collection.delete_one({"username": username})

def update_user(username, new_full_name, new_age, new_city):
    return collection.update_one(
        {"username": username},
        {"$set": {
            "full_name": new_full_name,
            "age": new_age,
            "city": new_city
        }}
    )

def grant_admin(username):
    return collection.update_one({"username": username}, {"$set": {"role": "admin"}})

def revoke_admin(username):
    return collection.update_one({"username": username}, {"$set": {"role": "user"}})

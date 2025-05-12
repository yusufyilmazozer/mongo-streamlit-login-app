import os
from pymongo import MongoClient
from gridfs import GridFS
import bcrypt
from bson import ObjectId
from dotenv import load_dotenv

# load .env variables
dotenv_path = os.path.join(os.path.dirname(__file__), os.pardir, ".env")
load_dotenv(dotenv_path)

# establish MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["user_db"]
collection = db["users"]
fs = GridFS(db)

# password hashing utilities
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode("utf-8"), hashed)

# GridFS helpers
def store_profile_image(file_obj, filename):
    contents = file_obj.read()
    content_type = getattr(file_obj, "type", None)
    return fs.put(contents, filename=filename, content_type=content_type)


def get_profile_image(image_id):
    if not image_id:
        return None
    grid_out = fs.get(ObjectId(str(image_id)))
    return grid_out.read()


def delete_profile_image_file(image_id):
    if not image_id:
        return
    try:
        fs.delete(ObjectId(str(image_id)))
    except Exception:
        pass

# User CRUD operations
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
        ext = profile_image.name.split('.')[-1]
        filename = f"{username}.{ext}"
        image_id = store_profile_image(profile_image, filename)
        user["profile_image_id"] = image_id
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
    user = find_user(username)
    return user.get("role", "user") if user else "user"


def delete_user(username):
    user = find_user(username)
    image_id = user.get("profile_image_id")
    if image_id:
        delete_profile_image_file(image_id)
    return collection.delete_one({"username": username})


def update_user(username, new_full_name, new_age, new_city):
    return collection.update_one(
        {"username": username},
        {"$set": {"full_name": new_full_name, "age": new_age, "city": new_city}}
    )


def grant_admin(username):
    return collection.update_one({"username": username}, {"$set": {"role": "admin"}})


def revoke_admin(username):
    return collection.update_one({"username": username}, {"$set": {"role": "user"}})

# new helper: update profile image for existing user
def update_profile_image(username, file_obj):
    """
    Replace a user's profile image in GridFS, removing the old one.
    Returns the new image_id.
    """
    user = find_user(username)
    if not user:
        return None
    old_id = user.get("profile_image_id")
    if old_id:
        delete_profile_image_file(old_id)
    ext = file_obj.name.split('.')[-1]
    filename = f"{username}.{ext}"
    new_id = store_profile_image(file_obj, filename)
    collection.update_one(
        {"username": username},
        {"$set": {"profile_image_id": new_id}}
    )
    return new_id

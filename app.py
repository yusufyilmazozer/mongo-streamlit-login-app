import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from bson import ObjectId

from utils.image_utils import delete_profile_image, crop_and_save_square_image
from database.db_utils import (
    add_user,
    get_all_users,
    login_user,
    get_user_role,
    find_user,
    update_user,
    delete_user,
    grant_admin,
    revoke_admin,
    collection
)

st.set_page_config(page_title="User Management", layout="centered")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

if not os.path.exists("uploads"):
    os.makedirs("uploads")

if not st.session_state.logged_in:
    menu = st.sidebar.selectbox("Menu", ["Login", "Register"])
else:
    menu = "Dashboard"

if menu == "Login":
    st.title("🔑 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"🎉 Welcome {user['full_name']}")
            st.rerun()
        else:
            st.error("❌ Login failed. Incorrect username or password.")

elif menu == "Register":
    st.title("📋 Register")

    username = st.text_input("Username")
    full_name = st.text_input("Full Name")
    age = st.number_input("Age", min_value=0, max_value=120)
    city = st.text_input("City")
    password = st.text_input("Password", type="password")
    profile_image = st.file_uploader("Upload Profile Image", type=["jpg", "jpeg", "png"])

    if st.button("Register"):
        if username and full_name and city and password:
            existing_user = collection.find_one({"username": username})
            if existing_user:
                st.error("❌ Username already taken.")
            else:
                image_path = None
                if profile_image is not None:
                    ext = profile_image.name.split(".")[-1]
                    new_id = ObjectId()
                    file_name = f"{new_id}.{ext}"
                    image_path = os.path.join("uploads", file_name)
                    crop_and_save_square_image(profile_image, image_path)

                add_user(username, full_name, age, city, password, profile_image=image_path)
                st.success("✅ Registration successful!")
        else:
            st.warning("Please fill in all fields.")

elif menu == "Dashboard" and st.session_state.logged_in:
    st.title("👤 User Dashboard")

    username = st.session_state.username
    role = get_user_role(username)
    user = find_user(username)

    col1, col2 = st.columns([1, 5])
    with col1:
        image_path = user.get("profile_image")
        if image_path and os.path.exists(image_path):
            st.image(image_path, width=100)
        else:
            st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=100)

    with col2:
        st.markdown(f"""
        **Full Name:** {user['full_name']}  
        **Age:** {user['age']}  
        **City:** {user['city']}  
        **Role:** {user.get('role', 'user')}
        """, unsafe_allow_html=True)

    if st.button("🔓 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

    if "edit_user" in st.session_state:
        edit_username = st.session_state.edit_user
        user = find_user(edit_username)

        st.subheader(f"🔧 Update {edit_username} Information")

        new_full_name = st.text_input("New Full Name", value=user["full_name"], key="edit_full_name")
        new_age = st.number_input("New Age", min_value=0, max_value=120, value=user["age"], key="edit_age")
        new_city = st.text_input("New City", value=user["city"], key="edit_city")

        if st.button("✅ Update"):
            update_user(edit_username, new_full_name, new_age, new_city)
            st.success("Information updated!")
            del st.session_state.edit_user
            st.rerun()

    st.subheader("📋 Registered Users")

    for u in get_all_users():
        u_username = u["username"]
        full_name = u["full_name"]
        u_role = u.get("role", "user")

        if u_username == st.session_state.username:
            continue

        col1, col2 = st.columns([1, 5])
        with col1:
            if "profile_image" in u:
                st.image(u["profile_image"], width=100)
            else:
                st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=100)

        with col2:
            st.markdown(f"""
            **Full Name:** {full_name}  
            **Age:** {u['age']}  
            **City:** {u['city']}  
            **Role:** {u_role}
            """, unsafe_allow_html=True)

            allow_actions = False

            if role == "super_admin":
                allow_actions = u_username != st.session_state.username
            elif role == "admin":
                allow_actions = u_role == "user"

            if allow_actions:
                col3, col4 = st.columns(2)
                with col3:
                    if st.button(f"📝 Edit - {full_name}", key=f"edit_{u_username}"):
                        st.session_state.edit_user = u_username
                        st.rerun()
                with col4:
                    if st.button(f"🗑️ Delete - {full_name}", key=f"delete_{u_username}"):
                        delete_user(u_username)
                        st.success(f"{full_name} deleted.")
                        st.rerun()

            if role == "super_admin" and u_username != st.session_state.username:
                if u_role == "user":
                    if st.button(f"⭐ Grant Admin - {full_name}", key=f"grant_admin_{u_username}"):
                        grant_admin(u_username)
                        st.success(f"{full_name} is now admin!")
                        st.rerun()
                elif u_role == "admin":
                    if st.button(f"🛑 Revoke Admin - {full_name}", key=f"revoke_admin_{u_username}"):
                        revoke_admin(u_username)
                        st.success(f"{full_name} is now a normal user.")
                        st.rerun()

    st.subheader("🛠️ Manage My Profile")

    user = find_user(st.session_state.username)

    st.markdown(f"**Username:** {user['username']}")

    new_full_name = st.text_input("Full Name", value=user["full_name"], key="profile_full_name")
    new_age = st.number_input("Age", min_value=0, max_value=120, value=user["age"], key="profile_age")
    new_city = st.text_input("City", value=user["city"], key="profile_city")
    new_profile_image = st.file_uploader("New Profile Image", type=["jpg", "jpeg", "png"], key="profile_image")

    if st.button("💾 Update My Info"):
        old_image = user.get("profile_image")
        if new_profile_image is not None and old_image:
            delete_profile_image(old_image)

        image_path = user.get("profile_image")
        if new_profile_image is not None:
            ext = new_profile_image.name.split(".")[-1]
            file_name = f"{user['_id']}.{ext}"
            image_path = os.path.join("uploads", file_name)
            crop_and_save_square_image(new_profile_image, image_path)

            with open(image_path, "wb") as f:
                f.write(new_profile_image.read())

        collection.update_one(
            {"username": st.session_state.username},
            {"$set": {
                "full_name": new_full_name,
                "age": new_age,
                "city": new_city,
                "profile_image": image_path
            }}
        )

        st.success("✅ Your profile has been updated!")
        st.rerun()

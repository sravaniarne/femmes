import streamlit as st
import sqlite3
import hashlib

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="FEMMES Job Recommendation System",
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .stApp {
        background: #ffffff;
        color: #000000;
    }
    h1 { font-family: 'Inter', sans-serif; color: #FF1493; text-align: center; }
    h3 { color: #000000; text-align: center; }
    .stTextInput label p, .stSelectbox label p { font-size: 18px !important; font-weight: bold !important; }
    .stButton > button {
        background: linear-gradient(90deg, #FF1493, #FF69B4);
        color: white; border: none; border-radius: 20px;
        padding: 10px 24px; font-size: 18px; font-weight: bold; width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #FF69B4, #FF1493);
    }
</style>
""", unsafe_allow_html=True)

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    conn = sqlite3.connect('femmes.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialization
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
    st.session_state['role'] = None
    st.session_state['username'] = None

# Routing block
if st.session_state['user_id'] is not None:
    role = st.session_state['role']
    if role == 'Seeker':
        st.switch_page("pages/1_Seeker_Dashboard.py")
    elif role == 'Recruiter':
        st.switch_page("pages/2_Recruiter_Dashboard.py")
    elif role == 'Admin':
        st.switch_page("pages/3_Admin_Dashboard.py")

st.markdown("<h1>FEMMES</h1>", unsafe_allow_html=True)
st.markdown("<h3>Your career starts here</h3>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Login", "Register"])

with tab1:
    st.header("Login")
    l_user = st.text_input("Username", key="l_user")
    l_pass = st.text_input("Password", type="password", key="l_pass")
    
    if st.button("Login 🚀"):
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (l_user, hash_pw(l_pass))).fetchone()
        conn.close()
        
        if user:
            st.session_state['user_id'] = user['id']
            st.session_state['role'] = user['role']
            st.session_state['username'] = user['username']
            st.success(f"Welcome back, {user['username']}!")
            st.rerun()
        else:
            st.error("Invalid username or password.")

with tab2:
    st.header("Register")
    r_user = st.text_input("Username", key="r_user")
    r_pass = st.text_input("Password", type="password", key="r_pass")
    r_role = st.selectbox("I am a:", ["Job Seeker", "Recruiter"])
    
    # Conditional fields based on role
    r_edu = None
    r_skills = None
    r_interests = None
    
    if r_role == "Job Seeker":
        r_edu = st.selectbox("Highest Education Level", ["10th", "Inter", "Degree", "B.Tech", "MBA"])
        r_skills = st.text_input("Your Skills (comma separated)", placeholder="e.g. Python, SQL, Communication")
        r_interests = st.text_input("Your Interests", placeholder="e.g. Technology, Management, Sales")
    
    if st.button("Create Account ✨"):
        if not r_user or not r_pass:
            st.warning("Please fill in Username and Password.")
        else:
            role_map = "Seeker" if r_role == "Job Seeker" else "Recruiter"
            conn = get_db_connection()
            try:
                conn.execute(
                    "INSERT INTO users (username, password, role, education, skills, interests) VALUES (?, ?, ?, ?, ?, ?)",
                    (r_user, hash_pw(r_pass), role_map, r_edu, r_skills, r_interests)
                )
                conn.commit()
                st.success("Account created successfully! You can now log in.")
                st.balloons()
            except sqlite3.IntegrityError:
                st.error("Username already exists. Please choose a different one.")
            finally:
                conn.close()

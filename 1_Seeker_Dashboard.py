import streamlit as st
import sqlite3
import joblib
import numpy as np
import os
import hashlib

st.set_page_config(page_title="Seeker Dashboard", page_icon="👩‍🎓", layout="wide")

# Auth Check
if 'user_id' not in st.session_state or st.session_state['role'] != 'Seeker':
    st.error("Access Denied. Please log in as a Job Seeker.")
    st.markdown("[Go to Login](/)")
    st.stop()

st.title(f"Welcome to your Dashboard, {st.session_state['username']}! 👋")

# Load Models
@st.cache_resource
def load_models():
    try:
        model = joblib.load('job_recommendation_model.pkl')
        user_vectorizer = joblib.load('user_vectorizer.pkl')
        job_vectorizer = joblib.load('job_vectorizer.pkl')
        return model, user_vectorizer, job_vectorizer
    except Exception as e:
        return None, None, None

model, user_vect, job_vect = load_models()

def get_db_connection():
    conn = sqlite3.connect('femmes.db')
    conn.row_factory = sqlite3.Row
    return conn

# Fetch user data
conn = get_db_connection()
user = conn.execute("SELECT * FROM users WHERE id = ?", (st.session_state['user_id'],)).fetchone()

# Education Map Info
edu_map = {
    "10th": "Helper jobs",
    "Inter": "Assistant jobs",
    "Degree": "Banking, Clerk jobs",
    "B.Tech": "IT jobs",
    "MBA": "Manager jobs"
}

st.markdown("---")

tab_jobs, tab_profile = st.tabs(["Dashboard & Jobs", "My Profile"])

with tab_profile:
    st.header("My Profile")
    st.write(f"- **Qualification:** {user['education']} ({edu_map.get(user['education'], 'Any')})")
    st.write(f"- **Skills:** {user['skills']}")
    st.write(f"- **Interests:** {user['interests']}")
    
    st.markdown("---")
    st.subheader("Edit Profile")
    with st.form("edit_profile_form"):
        new_username = st.text_input("Username", value=user['username'])
        new_password = st.text_input("New Password (leave blank to keep current)", type="password")
        new_edu = st.selectbox("Highest Education Level", ["10th", "Inter", "Degree", "B.Tech", "MBA"], index=["10th", "Inter", "Degree", "B.Tech", "MBA"].index(user['education']) if user['education'] in ["10th", "Inter", "Degree", "B.Tech", "MBA"] else 0)
        new_skills = st.text_input("Your Skills (comma separated)", value=user['skills'] if user['skills'] else "")
        new_interests = st.text_input("Your Interests", value=user['interests'] if user['interests'] else "")
        
        submitted = st.form_submit_button("Update Profile")
        if submitted:
            conn_update = get_db_connection()
            try:
                if new_password:
                    hashed_pw = hashlib.sha256(new_password.encode()).hexdigest()
                    conn_update.execute("UPDATE users SET username=?, password=?, education=?, skills=?, interests=? WHERE id=?", 
                                 (new_username, hashed_pw, new_edu, new_skills, new_interests, st.session_state['user_id']))
                else:
                    conn_update.execute("UPDATE users SET username=?, education=?, skills=?, interests=? WHERE id=?", 
                                 (new_username, new_edu, new_skills, new_interests, st.session_state['user_id']))
                conn_update.commit()
                st.session_state['username'] = new_username
                st.success("Profile updated successfully!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Username already exists. Please choose a different one.")
            finally:
                conn_update.close()

with tab_jobs:
    st.subheader("🎯 Recommended Jobs for You")

# Get jobs matching the user's education tier constraints
jobs = conn.execute("SELECT * FROM jobs WHERE education_category = ?", (user['education'],)).fetchall()

if not jobs:
    st.info("No jobs currently available for your education qualification level. Please check back later!")
else:
    if model is None:
        st.warning("ML Recommendation Engine is offline. Displaying all matching category jobs.")
        for job in jobs:
            st.markdown(f"### {job['title']}")
            st.write(f"**Skills Required:** {job['req_skills']}")
            st.write(f"{job['description']}")
            st.button(f"Apply for {job['title']}", key=f"apply_{job['id']}")
    else:
        # Rank jobs with ML model
        recommendations = []
        combined_user_profile = f"{user['skills']} {user['education']} {user['interests']}"
        X_user = user_vect.transform([combined_user_profile]).toarray()
        
        for job in jobs:
            X_job = job_vect.transform([job['req_skills']]).toarray()
            X_test = np.hstack((X_user, X_job))
            
            pred = model.predict(X_test)[0]
            prob = model.predict_proba(X_test)[0]
            match_prob = prob[1] * 100 if len(model.classes_) == 2 else (100 if pred == 1 else 0)
            
            recommendations.append((job, match_prob))
        
        # Sort by best match
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        # Display
        cols = st.columns(2)
        for i, (job, score) in enumerate(recommendations):
            with cols[i % 2]:
                st.markdown(f"<div style='border:1px solid #ddd; padding:15px; border-radius:10px; margin-bottom:15px;'>"
                            f"<h4>{job['title']} <span style='color:#FF1493; font-size:16px;'>(Match: {score:.1f}%)</span></h4>"
                            f"<p><b>Required Skills:</b> {job['req_skills']}</p>"
                            f"<p>{job['description']}</p>"
                            f"</div>", unsafe_allow_html=True)
                
                # Apply functionality
                st.write("Upload Resume to Apply:")
                resume_file = st.file_uploader("Resume (PDF/Doc)", key=f"file_{job['id']}", label_visibility="collapsed")
                
                if st.button(f"Submit Application", key=f"btn_{job['id']}"):
                    if resume_file is None:
                        st.error("Please upload a resume to apply.")
                    else:
                        # Save resume
                        os.makedirs("resumes", exist_ok=True)
                        resume_path = os.path.join("resumes", f"{user['id']}_{job['id']}_{resume_file.name}")
                        with open(resume_path, "wb") as f:
                            f.write(resume_file.getbuffer())
                        
                        # Add to DB
                        try:
                            # Check if already applied
                            existing = conn.execute("SELECT id FROM applications WHERE seeker_id = ? AND job_id = ?", 
                                                    (user['id'], job['id'])).fetchone()
                            if existing:
                                st.warning("You have already applied for this job.")
                            else:
                                conn.execute("INSERT INTO applications (job_id, seeker_id, resume_path) VALUES (?, ?, ?)",
                                             (job['id'], user['id'], resume_path))
                                conn.commit()
                                st.success("Application Submitted Successfully!")
                        except Exception as e:
                            st.error(f"Error: {e}")

conn.close()

st.sidebar.markdown(f"**Logged in as {st.session_state['username']}**")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

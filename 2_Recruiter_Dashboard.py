import streamlit as st
import sqlite3
import pandas as pd
import joblib
import numpy as np
import os
import hashlib

st.set_page_config(page_title="Recruiter Dashboard", page_icon="🏢", layout="wide")

# Auth Check
if 'user_id' not in st.session_state or st.session_state['role'] != 'Recruiter':
    st.error("Access Denied. Please log in as a Recruiter.")
    st.markdown("[Go to Login](/)")
    st.stop()

def get_db_connection():
    conn = sqlite3.connect('femmes.db')
    conn.row_factory = sqlite3.Row
    return conn

st.title(f"Recruiter Dashboard - {st.session_state['username']}")

tab1, tab2, tab3 = st.tabs(["Post a Job", "Review Applications", "My Profile"])

# Load ML Model for scoring applicants
@st.cache_resource
def load_models():
    try:
        model = joblib.load('job_recommendation_model.pkl')
        user_vectorizer = joblib.load('user_vectorizer.pkl')
        job_vectorizer = joblib.load('job_vectorizer.pkl')
        return model, user_vectorizer, job_vectorizer
    except:
        return None, None, None

model, user_vect, job_vect = load_models()

with tab1:
    st.header("Post a New Job Opportunity")
    with st.form("post_job_form"):
        title = st.text_input("Job Title", placeholder="e.g. Senior Software Engineer")
        edu_cat = st.selectbox("Target Education Level", ["10th", "Inter", "Degree", "B.Tech", "MBA"], 
                               help="10th: Helper, Inter: Assistant, Degree: Clerk/Bank, B.Tech: IT, MBA: Manager")
        req_skills = st.text_input("Required Skills", placeholder="e.g. Python, SQL, Cloud Computing")
        description = st.text_area("Job Description", placeholder="Brief description of responsibilities...")
        
        submitted = st.form_submit_button("Post Job")
        if submitted:
            if not title or not req_skills:
                st.error("Title and Required Skills are mandatory.")
            else:
                conn = get_db_connection()
                conn.execute(
                    "INSERT INTO jobs (recruiter_id, title, description, education_category, req_skills) VALUES (?, ?, ?, ?, ?)",
                    (st.session_state['user_id'], title, description, edu_cat, req_skills)
                )
                conn.commit()
                conn.close()
                st.success(f"Job '{title}' posted successfully!")

with tab2:
    st.header("Review Applications")
    conn = get_db_connection()
    
    # Get all jobs posted by this recruiter
    my_jobs = conn.execute("SELECT id, title, req_skills FROM jobs WHERE recruiter_id = ?", (st.session_state['user_id'],)).fetchall()
    
    if not my_jobs:
        st.info("You haven't posted any jobs yet.")
    else:
        job_options = {j['id']: j['title'] for j in my_jobs}
        selected_job_id = st.selectbox("Select a Job to view applicants", options=list(job_options.keys()), format_func=lambda x: job_options[x])
        
        if selected_job_id:
            # Find req_skills for this job to use in ML scoring
            req_skills = next(j['req_skills'] for j in my_jobs if j['id'] == selected_job_id)
            
            apps = conn.execute("""
                SELECT a.id as app_id, a.resume_path, a.status, u.username, u.education, u.skills, u.interests 
                FROM applications a
                JOIN users u ON a.seeker_id = u.id
                WHERE a.job_id = ?
            """, (selected_job_id,)).fetchall()
            
            if not apps:
                st.write("No applications for this job yet.")
            else:
                for app in apps:
                    with st.expander(f"Applicant: {app['username']} (Status: {app['status']})"):
                        st.write(f"**Education:** {app['education']}")
                        st.write(f"**Skills:** {app['skills']}")
                        st.write(f"**Interests:** {app['interests']}")
                        
                        # Calculate Match Score
                        if model is not None:
                            combined_user_profile = f"{app['skills']} {app['education']} {app['interests']}"
                            X_user = user_vect.transform([combined_user_profile]).toarray()
                            X_job = job_vect.transform([req_skills]).toarray()
                            X_test = np.hstack((X_user, X_job))
                            
                            pred = model.predict(X_test)[0]
                            prob = model.predict_proba(X_test)[0]
                            match_prob = prob[1] * 100 if len(model.classes_) == 2 else (100 if pred == 1 else 0)
                            
                            score_color = "green" if pred == 1 else "red"
                            st.markdown(f"**AI Match Score:** <span style='color:{score_color}; font-weight:bold;'>{match_prob:.1f}%</span>", unsafe_allow_html=True)
                        
                        if app['resume_path'] and os.path.exists(app['resume_path']):
                            with open(app['resume_path'], "rb") as f:
                                st.download_button("Download Resume", f, file_name=os.path.basename(app['resume_path']))
                        else:
                            st.write("No resume file available.")
                            
                        # Actions
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Accept Candidate", key=f"acc_{app['app_id']}"):
                                conn.execute("UPDATE applications SET status = 'Accepted' WHERE id = ?", (app['app_id'],))
                                conn.commit()
                                st.success("Candidate Accepted!")
                                st.rerun()
                        with col2:
                            if st.button("Reject Candidate", key=f"rej_{app['app_id']}"):
                                conn.execute("UPDATE applications SET status = 'Rejected' WHERE id = ?", (app['app_id'],))
                                conn.commit()
                                st.error("Candidate Rejected.")
                                st.rerun()
    conn.close()

with tab3:
    st.header("My Profile")
    conn_profile = get_db_connection()
    user = conn_profile.execute("SELECT * FROM users WHERE id = ?", (st.session_state['user_id'],)).fetchone()
    conn_profile.close()
    
    with st.form("edit_recruiter_profile"):
        new_username = st.text_input("Username", value=user['username'])
        new_password = st.text_input("New Password (leave blank to keep current)", type="password")
        
        submitted = st.form_submit_button("Update Profile")
        if submitted:
            conn_update = get_db_connection()
            try:
                if new_password:
                    hashed_pw = hashlib.sha256(new_password.encode()).hexdigest()
                    conn_update.execute("UPDATE users SET username=?, password=? WHERE id=?", 
                                 (new_username, hashed_pw, st.session_state['user_id']))
                else:
                    conn_update.execute("UPDATE users SET username=? WHERE id=?", 
                                 (new_username, st.session_state['user_id']))
                conn_update.commit()
                st.session_state['username'] = new_username
                st.success("Profile updated successfully!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Username already exists. Please choose a different one.")
            finally:
                conn_update.close()

st.sidebar.markdown(f"**Logged in as {st.session_state['username']}**")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

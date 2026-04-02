import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Admin Dashboard", page_icon="🛡️", layout="wide")

# Auth Check
if 'user_id' not in st.session_state or st.session_state['role'] != 'Admin':
    st.error("Access Denied. Please log in as an Administrator.")
    st.markdown("[Go to Login](/)")
    st.stop()

def get_db_connection():
    conn = sqlite3.connect('femmes.db')
    conn.row_factory = sqlite3.Row
    return conn

st.title("Admin Dashboard")

tab1, tab2, tab3 = st.tabs(["Manage Users", "Manage Jobs", "View App Stats"])

with tab1:
    st.header("Platform Users")
    conn = get_db_connection()
    users = conn.execute("SELECT id, username, role, education FROM users").fetchall()
    
    if users:
        df_users = pd.DataFrame([dict(u) for u in users])
        st.dataframe(df_users, use_container_width=True)
        
        st.subheader("Remove User")
        del_target = st.selectbox("Select User ID to Delete", df_users['id'])
        if st.button("Delete User", type="primary"):
            if del_target == st.session_state['user_id']:
                st.error("You cannot delete your own Admin account.")
            else:
                conn.execute("DELETE FROM users WHERE id = ?", (del_target,))
                conn.commit()
                st.success(f"User {del_target} deleted.")
                st.rerun()
    else:
        st.write("No users found.")
    conn.close()

with tab2:
    st.header("Platform Jobs")
    conn = get_db_connection()
    jobs = conn.execute("SELECT id, recruiter_id, title, education_category FROM jobs").fetchall()
    
    if jobs:
        df_jobs = pd.DataFrame([dict(j) for j in jobs])
        st.dataframe(df_jobs, use_container_width=True)
        
        st.subheader("Remove Job Posting")
        del_job = st.selectbox("Select Job ID to Delete", df_jobs['id'])
        if st.button("Delete Job", type="primary"):
            conn.execute("DELETE FROM jobs WHERE id = ?", (del_job,))
            # Delete associated applications
            conn.execute("DELETE FROM applications WHERE job_id = ?", (del_job,))
            conn.commit()
            st.success(f"Job {del_job} deleted.")
            st.rerun()
    else:
        st.write("No jobs posted yet.")
    conn.close()

with tab3:
    st.header("Application Statistics")
    conn = get_db_connection()
    apps = conn.execute("""
        SELECT a.id, j.title as job_title, u.username as applicant, a.status 
        FROM applications a 
        JOIN jobs j ON a.job_id = j.id 
        JOIN users u ON a.seeker_id = u.id
    """).fetchall()
    
    if apps:
        df_apps = pd.DataFrame([dict(a) for a in apps])
        st.dataframe(df_apps, use_container_width=True)
        
        # Simple stats
        st.write(f"**Total Applications:** {len(df_apps)}")
        st.write("**By Status:**")
        st.write(df_apps['status'].value_counts())
    else:
        st.write("No applications submitted yet.")
    conn.close()

st.sidebar.markdown(f"**Logged in as {st.session_state['username']}**")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

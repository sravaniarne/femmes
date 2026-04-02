import sqlite3
import os

def init_db():
    conn = sqlite3.connect('femmes.db')
    c = conn.cursor()

    # Create Users Table
    # roles: Seeker, Recruiter, Admin
    # education: 10th, Inter, Degree, B.Tech, MBA
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            education TEXT,
            skills TEXT,
            interests TEXT
        )
    ''')

    # Create Jobs Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recruiter_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            education_category TEXT NOT NULL,
            req_skills TEXT,
            FOREIGN KEY (recruiter_id) REFERENCES users (id)
        )
    ''')

    # Create Applications Table
    # status: Pending, Accepted, Rejected
    c.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            seeker_id INTEGER NOT NULL,
            resume_path TEXT,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (job_id) REFERENCES jobs (id),
            FOREIGN KEY (seeker_id) REFERENCES users (id)
        )
    ''')
    
    # Add an admin user if it doesn't exist
    import hashlib
    admin_pw = hashlib.sha256("admin".encode()).hexdigest()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  ("admin", admin_pw, "Admin"))
    except sqlite3.IntegrityError:
        pass # Admin already exists

    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()

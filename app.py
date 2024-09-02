import streamlit as st
import pandas as pd
import hashlib
import json
import sqlite3

# Utility functions

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

# Database functions
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        st.error(f"Database connection error: {e}")
    return conn

def create_tables(conn):
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY,
                        password TEXT NOT NULL,
                        role TEXT NOT NULL
                    );''')
        c.execute('''CREATE TABLE IF NOT EXISTS students (
                        username TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        roll_no TEXT NOT NULL,
                        phone TEXT CHECK(length(phone) == 10),
                        test_marks TEXT NOT NULL,
                        certifications TEXT,
                        projects TEXT,
                        academic_issues TEXT,
                        FOREIGN KEY (username) REFERENCES users (username)
                    );''')
        c.execute('''CREATE TABLE IF NOT EXISTS feedback (
                        mentor_username TEXT NOT NULL,
                        student_username TEXT NOT NULL,
                        feedback TEXT NOT NULL,
                        FOREIGN KEY (mentor_username) REFERENCES users (username),
                        FOREIGN KEY (student_username) REFERENCES users (username)
                    );''')
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error creating tables: {e}")

def save_user_data(user_data, conn):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  (user_data['username'], user_data['password'], user_data['role']))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error saving user data: {e}")

def load_user_data(conn):
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        rows = c.fetchall()
        return pd.DataFrame(rows, columns=['username', 'password', 'role'])
    except sqlite3.Error as e:
        st.error(f"Error loading user data: {e}")
        return pd.DataFrame(columns=['username', 'password', 'role'])

def save_student_details(student_details, conn):
    try:
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO students (username, name, roll_no, phone, test_marks, certifications, projects, academic_issues) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                  (student_details['username'], student_details['name'], student_details['roll_no'], 
                   student_details['phone'], student_details['test_marks'], student_details['certifications'], 
                   student_details['projects'], student_details['academic_issues']))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error saving student details: {e}")

def load_student_details(conn, username=None, roll_no=None):
    try:
        c = conn.cursor()
        if username:
            c.execute("SELECT * FROM students WHERE username = ?", (username,))
        elif roll_no:
            c.execute("SELECT * FROM students WHERE roll_no = ?", (roll_no,))
        else:
            c.execute("SELECT * FROM students")
        rows = c.fetchall()
        return pd.DataFrame(rows, columns=['username', 'name', 'roll_no', 'phone', 'test_marks', 
                                           'certifications', 'projects', 'academic_issues'])
    except sqlite3.Error as e:
        st.error(f"Error loading student details: {e}")
        return pd.DataFrame(columns=['username', 'name', 'roll_no', 'phone', 'test_marks', 
                                     'certifications', 'projects', 'academic_issues'])

def save_feedback(feedback_data, conn):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO feedback (mentor_username, student_username, feedback) VALUES (?, ?, ?)", 
                  (feedback_data['mentor_username'], feedback_data['student_username'], feedback_data['feedback']))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error saving feedback: {e}")

def load_feedback(conn):
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM feedback")
        rows = c.fetchall()
        return pd.DataFrame(rows, columns=['mentor_username', 'student_username', 'feedback'])
    except sqlite3.Error as e:
        st.error(f"Error loading feedback: {e}")
        return pd.DataFrame(columns=['mentor_username', 'student_username', 'feedback'])

def delete_student(roll_no, conn):
    try:
        c = conn.cursor()
        
        # First, fetch the username associated with the given roll number
        c.execute("SELECT username FROM students WHERE roll_no = ?", (roll_no,))
        username = c.fetchone()
        
        if username:
            username = username[0]
            
            # Delete related feedback entries
            c.execute("DELETE FROM feedback WHERE student_username = ?", (username,))
            
            # Delete from users table
            c.execute("DELETE FROM users WHERE username = ?", (username,))
            
            # Delete from students table
            c.execute("DELETE FROM students WHERE roll_no = ?", (roll_no,))
            
            conn.commit()
            st.success("Student and related data removed successfully!")
        else:
            st.error("No student found with the provided roll number.")
            
    except sqlite3.Error as e:
        st.error(f"Error deleting student: {e}")


def add_background():
    # Add your background image URL here
    background_image_url = "https://th.bing.com/th/id/R.5e808ce28c3614e93d7989cf9f8e1743?rik=ONqobzODJm2T3Q&"
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: url({background_image_url});
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Streamlit app
def main():
    conn = create_connection("mentor_mentee_app.db")
    create_tables(conn)

    # Add background image
    add_background()
    
    # Initialize session state variables
    if 'page' not in st.session_state:
        st.session_state['page'] = 'Home'
    if 'login_status' not in st.session_state:
        st.session_state['login_status'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = ''
    if 'role' not in st.session_state:
        st.session_state['role'] = ''
    if 'selected_student' not in st.session_state:
        st.session_state['selected_student'] = None
    if 'subjects' not in st.session_state:
        st.session_state['subjects'] = []

    def go_to_page(page_name):
        st.session_state['page'] = page_name
        st.experimental_rerun()

    if st.session_state['page'] == 'Home':
        st.subheader("Home")
        st.write("Welcome to the Mentor-Mentee App.")
        if st.button("Go to Login"):
            go_to_page('Login')
        if st.button("Go to SignUp"):
            go_to_page('SignUp')

    elif st.session_state['page'] == 'SignUp':
        st.subheader("Create New Account")
        username = st.text_input("User Name")
        password = st.text_input("Password", type='password')
        role = st.selectbox("Role", ["Mentor", "Student"])

        if st.button("Signup"):
            if not username or not password:
                st.error("Username and password are required!")
            else:
                hashed_password = make_hashes(password)
                user_data = {'username': username, 'password': hashed_password, 'role': role}
                save_user_data(user_data, conn)
                st.success("You have successfully created an account")
                st.info("Go to Login Menu to login")
        if st.button("Back to Home"):
            go_to_page('Home')

    elif st.session_state['page'] == 'Login':
        st.subheader("Login Section")
        username = st.text_input("User Name")
        password = st.text_input("Password", type='password')
        role = st.selectbox("Role", ["Mentor", "Student"])

        if st.button("Login"):
            user_data = load_user_data(conn)
            if username in user_data['username'].values:
                hashed_password = make_hashes(password)
                if check_hashes(password, user_data[user_data['username'] == username]['password'].values[0]) and user_data[user_data['username'] == username]['role'].values[0] == role:
                    st.session_state['login_status'] = True
                    st.session_state['username'] = username
                    st.session_state['role'] = role
                    st.success(f"Logged In as {role}")
                    if role == 'Student':
                        go_to_page('Student')
                    else:
                        go_to_page('Mentor')
                else:
                    st.warning("Incorrect Role/Password")
            else:
                st.warning("Username not found")
        if st.button("Back to Home"):
            go_to_page('Home')

    if st.session_state['login_status']:
        if st.session_state['page'] == 'Student':
            st.subheader("Student Details Form")
            students_data = load_student_details(conn, st.session_state['username'])
            if not students_data.empty:
                student_data = students_data.iloc[0]
                name = st.text_input("Name", value=student_data['name'])
                roll_no = st.text_input("Roll Number", value=student_data['roll_no'])
                phone = st.text_input("Phone Number", value=str(student_data['phone']))
                certifications = st.text_area("Certifications", value=student_data['certifications'])
                projects = st.text_area("Projects", value=student_data['projects'])
                academic_issues = st.text_area("Academic Issues", value=student_data['academic_issues'])
                test_marks = json.loads(student_data['test_marks'])
            else:
                name = st.text_input("Name")
                roll_no = st.text_input("Roll Number")
                phone = st.text_input("Phone Number")
                certifications = st.text_area("Certifications")
                projects = st.text_area("Projects")
                academic_issues = st.text_area("Academic Issues")
                test_marks = []

            num_semesters = st.number_input("Number of Semesters", min_value=0, max_value=10, value=len(test_marks))

            if len(test_marks) < num_semesters:
                for _ in range(len(test_marks), num_semesters):
                    test_marks.append({'semester': len(test_marks) + 1, 'subjects': [], 'backlogs': 0})
            elif len(test_marks) > num_semesters:
                test_marks = test_marks[:num_semesters]

            for i in range(num_semesters):
                st.subheader(f"Semester {i + 1}")

                num_subjects = st.number_input(f"Number of Subjects for Semester {i + 1}", min_value=1, max_value=10, 
                                                value=max(len(test_marks[i]['subjects']), 1), key=f"num_subjects_{i}")

                if len(test_marks[i]['subjects']) < num_subjects:
                    for _ in range(len(test_marks[i]['subjects']), num_subjects):
                        test_marks[i]['subjects'].append({'subject': '', 'marks': ''})
                elif len(test_marks[i]['subjects']) > num_subjects:
                    test_marks[i]['subjects'] = test_marks[i]['subjects'][:num_subjects]

                subjects = []
                cols = st.columns(2)
                for j in range(num_subjects):
                    with cols[0]:
                        subject_name = st.text_input(f"Subject {j + 1}", value=test_marks[i]['subjects'][j].get('subject', ''), key=f"subject_{i}_{j}")
                    with cols[1]:
                        marks = st.text_input(f"Marks {j + 1}", value=test_marks[i]['subjects'][j].get('marks', ''), key=f"marks_{i}_{j}")
                    subjects.append({'subject': subject_name, 'marks': marks})

                with st.expander(f"Backlogs for Semester {i + 1}"):
                    backlogs = st.number_input(f"Backlogs", min_value=0, max_value=10, 
                                              value=test_marks[i].get('backlogs', 0), key=f"backlogs_{i}")

                semester_data = {'semester': i + 1, 'subjects': subjects, 'backlogs': backlogs}
                test_marks[i] = semester_data

            if st.button("Submit Details"):
                student_details = {
                    'username': st.session_state['username'],
                    'name': name,
                    'roll_no': roll_no,
                    'phone': phone,
                    'test_marks': json.dumps(test_marks),
                    'certifications': certifications,
                    'projects': projects,
                    'academic_issues': academic_issues
                }
                save_student_details(student_details, conn)
                st.success("Details Submitted Successfully")

            st.subheader("Mentor Feedback")
            feedback_data = load_feedback(conn)
            student_feedback = feedback_data[feedback_data['student_username'] == st.session_state['username']]
            if not student_feedback.empty:
                for _, feedback in student_feedback.iterrows():
                    st.write(f"Mentor: {feedback['mentor_username']}")
                    st.write(f"Feedback: {feedback['feedback']}")
                    st.write("---")
            else:
                st.write("No feedback available yet.")

        elif st.session_state['page'] == 'Mentor':
            st.subheader("Mentor Page")
            
            # Search for a student by roll number
            roll_no = st.text_input("Search Student by Roll Number")
            if roll_no:
                student_data = load_student_details(conn, roll_no=roll_no)
                if not student_data.empty:
                    st.write("Student Details:")
                    student_data = student_data.iloc[0]
                    st.write(f"Name: {student_data['name']}")
                    st.write(f"Roll Number: {student_data['roll_no']}")
                    st.write(f"Phone Number: {student_data['phone']}")
                    st.write(f"Certifications: {student_data['certifications']}")
                    st.write(f"Projects: {student_data['projects']}")
                    st.write(f"Academic Issues: {student_data['academic_issues']}")
                    
                    # Display marks
                    test_marks = json.loads(student_data['test_marks'])
                    for semester in test_marks:
                        st.subheader(f"Semester {semester['semester']} Marks")
                        for subject in semester['subjects']:
                            st.write(f"Subject: {subject['subject']}, Marks: {subject['marks']}")
                        st.write(f"Backlogs: {semester['backlogs']}")
                    
                    
                    # Provide feedback functionality
                    feedback = st.text_area("Feedback for the student", height=200)
                    if st.button("Submit Feedback"):
                        if feedback:
                            feedback_data = {
                                'mentor_username': st.session_state['username'],
                                'student_username': student_data['username'],
                                'feedback': feedback
                            }
                            save_feedback(feedback_data, conn)
                            st.success("Feedback Submitted Successfully")
                        else:
                            st.error("Please enter feedback.")
                    if st.button("Remove Student"):
                        if roll_no:
                            delete_student(roll_no, conn)
                            st.success("Student removed successfully!")
                else:
                    st.write("No student found with this roll number.")
            else:
                st.write("Please enter a roll number to search.")
            
            

        if st.button("Logout"):
            st.session_state['login_status'] = False
            st.session_state['username'] = ''
            st.session_state['role'] = ''
            st.session_state['subjects'] = []
            go_to_page('Home')

if __name__ == "__main__":
    main()

from openai import OpenAI
import streamlit as st
import sqlite3
from sqlite3 import Error
import re

# Initializing OpenAI client
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama',  # required, but unused
)

# Function to generate model predictions using OpenAI client
def predict(message, history):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ] + [{"role": "user", "content": h[0]}, {"role": "assistant", "content": h[1]} for h in history] + [{"role": "user", "content": message}]
    
    response = client.chat.completions.create(
        model="llama2",
        messages=messages
    )
    return response.choices[0].message.content

# Function to create a SQLite connection.
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(':memory:')  # Creates an in-memory SQLite database.
        print(sqlite3.version)
    except Error as e:
        print(e)
    return conn

# Function to create a table in the SQLite database.
def create_table(conn):
    try:
        sql = '''CREATE TABLE activities(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    day INTEGER,
                    steps_walked INTEGER,
                    hours_slept REAL,
                    water_intake REAL,
                    exercise_duration REAL,
                    mood TEXT,
                    calories_intake INTEGER,
                    productivity_score INTEGER,
                    work_done TEXT
                );'''
        conn.execute(sql)
    except Error as e:
        print(e)

# Function to insert activities into the SQLite database.
def insert_activities(conn, activities):
    sql = '''INSERT INTO activities(day, steps_walked, hours_slept, water_intake, exercise_duration, mood, calories_intake, productivity_score, work_done)
             VALUES(?,?,?,?,?,?,?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, activities)
    conn.commit()
    return cur.lastrowid

# Function to retrieve activities from the SQLite database.
def select_activities(conn, day):
    cur = conn.cursor()
    cur.execute("SELECT * FROM activities WHERE day=?", (day,))
    rows = cur.fetchall()
    return rows

# Function to parse user input for logging activities.
def parse_activity_input(message):
    activity_data = {}
    patterns = {
        'steps_walked': r"(\d+) steps",
        'hours_slept': r"(\d+(\.\d+)?) hours of sleep",
        'water_intake': r"(\d+(\.\d+)?) liters of water",
        'exercise_duration': r"(\d+) minutes of exercise",
        'mood': r"(Excellent|Good|Neutral|Bad|Very Bad) mood",
        'calories_intake': r"(\d+) calories",
        'productivity_score': r"productivity score of (\d+)",
        'work_done': r"work done: (.+)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, message)
        if match:
            activity_data[key] = match.group(1) if key != 'mood' else match.group(0)

    return activity_data

# Streamlit interface
def main():
    st.title("OpenAI ChatBot Activity Tracker")
    st.write("Ask the assistant any questions or input your daily activities.")
    message = st.text_input('Enter your message')
    history = []  # You can update this as per your requirement
    if st.button('Send'):
        response = predict(message, history)
        st.write(response)
        activity_data = parse_activity_input(response)
        if activity_data:
            day = st.number_input('Enter the day', min_value=1)
            conn = create_connection()
            create_table(conn)
            activities = (day, int(activity_data.get('steps_walked', 0)), float(activity_data.get('hours_slept', 0)),
                          float(activity_data.get('water_intake', 0)), int(activity_data.get('exercise_duration', 0)),
                          activity_data.get('mood', ''), int(activity_data.get('calories_intake', 0)),
                          int(activity_data.get('productivity_score', 0)), activity_data.get('work_done', ''))
            insert_activities(conn, activities)
            st.write("Activity data logged successfully.")
    conn = create_connection()
    create_table(conn)
    day = st.number_input('Enter the day to retrieve activities', min_value=1)
    if st.button('Show activities'):
        activities = select_activities(conn, day)
        for activity in activities:
            st.write(activity)

if __name__ == "__main__":
    main()

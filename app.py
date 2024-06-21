import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import StoppingCriteria, StoppingCriteriaList, TextIteratorStreamer
from threading import Thread
import streamlit as st
import sqlite3
from sqlite3 import Error
import re

tokenizer = AutoTokenizer.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
model = AutoModelForCausalLM.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)

class StopOnTokens(StoppingCriteria):
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        stop_ids = [2]  
        for stop_id in stop_ids:
            if input_ids[0][-1] == stop_id:  
                return True
        return False

def predict(message, history):
    history_transformer_format = history + [[message, ""]]
    stop = StopOnTokens()

    # Formatting the input for the model.
    messages = "</s>".join(["</s>".join(["\n:" + item[0], "\n:" + item[1]]) for item in history_transformer_format])
    model_inputs = tokenizer([messages], return_tensors="pt").to(device)
    streamer = TextIteratorStreamer(tokenizer, timeout=10.0, skip_prompt=True, skip_special_tokens=True)
    generate_kwargs = dict(
        input_ids=model_inputs['input_ids'],
        attention_mask=model_inputs['attention_mask'],
        streamer=streamer,
        max_new_tokens=1024,
        do_sample=True,
        top_p=0.95,
        top_k=50,
        temperature=0.7,
        num_beams=1,
        stopping_criteria=StoppingCriteriaList([stop])
    )
    t = Thread(target=model.generate, kwargs=generate_kwargs)
    t.start()  
    partial_message = ""
    for new_token in streamer:
        partial_message += new_token
        if '</s>' in partial_message:  # Breaking the loop if the stop token is generated.
            break
        yield partial_message

# Function to create a SQLite connection.
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(':memory:')  # Creates an in-memory SQLite database.
        print(sqlite3.version)
    except Error as e:
        print(e)
    return conn

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

def main():
    st.title("TinyLlama ChatBot")
    st.write("Ask TinyLlama any questions or input your daily activities.")
    message = st.text_input('Enter your message')
    history = []
    if st.button('Send'):
        response = predict(message, history)
        response_text = "".join([r for r in response])
        st.write(response_text)
        activity_data = parse_activity_input(response_text)
        if activity_data:
            day = st.number_input('Enter the day', min_value=1)
            conn = create_connection()
            create_table(conn)
            activities = (day, activity_data.get('steps_walked', 0), activity_data.get('hours_slept', 0), 
                          activity_data.get('water_intake', 0), activity_data.get('exercise_duration', 0), 
                          activity_data.get('mood', ''), activity_data.get('calories_intake', 0), 
                          activity_data.get('productivity_score', 0), activity_data.get('work_done', ''))
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

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import StoppingCriteria, StoppingCriteriaList, TextIteratorStreamer
from threading import Thread
import streamlit as st

# Loading the tokenizer and model from Hugging Face's model hub.
tokenizer = AutoTokenizer.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
model = AutoModelForCausalLM.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")

# using CUDA for an optimal experience
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)


# Defining a custom stopping criteria class for the model's text generation.
class StopOnTokens(StoppingCriteria):
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        stop_ids = [2]  # IDs of tokens where the generation should stop.
        for stop_id in stop_ids:
            if input_ids[0][-1] == stop_id:  # Checking if the last generated token is a stop token.
                return True
        return False


# Function to generate model predictions.
def predict(message, history):
    history_transformer_format = history + [[message, ""]]
    stop = StopOnTokens()

    # Formatting the input for the model.
    messages = "</s>".join(["</s>".join(["\n<|user|>:" + item[0], "\n<|assistant|>:" + item[1]])
                        for item in history_transformer_format])
    model_inputs = tokenizer([messages], return_tensors="pt").to(device)
    streamer = TextIteratorStreamer(tokenizer, timeout=10., skip_prompt=True, skip_special_tokens=True)
    generate_kwargs = dict(
        model_inputs,
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
    t.start()  # Starting the generation in a separate thread.
    partial_message = ""
    for new_token in streamer:
        partial_message += new_token
        if '</s>' in partial_message:  # Breaking the loop if the stop token is generated.
            break
        yield partial_message

import sqlite3
from sqlite3 import Error

# Function to create a SQLite connection.
def create_connection():
    conn = None;
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

# Function to track daily activities.
def track_activities(conn, day):
    steps_walked = st.number_input('Enter steps walked today', min_value=0)
    hours_slept = st.number_input('Enter hours of sleep', min_value=0)
    water_intake = st.number_input('Enter water intake in liters', min_value=0.0)
    exercise_duration = st.number_input('Enter exercise duration in minutes', min_value=0)
    mood = st.selectbox('How was your mood today?', ['Excellent', 'Good', 'Neutral', 'Bad', 'Very Bad'])
    calories_intake = st.number_input('Enter calories intake', min_value=0)
    productivity_score = st.slider('Rate your productivity today', min_value=0, max_value=10)
    work_done = st.text_input('Enter work done today')
    activities = (day, steps_walked, hours_slept, water_intake, exercise_duration, mood, calories_intake, productivity_score, work_done)
    insert_activities(conn, activities)

# Streamlit interface
def main():
    st.title("Tinyllama_chatBot")
    st.write("Ask Tiny llama any questions")
    message = st.text_input('Enter your message')
    history = []  # You can update this as per your requirement
    if st.button('Send'):
        response = predict(message, history)
        st.write(response)
    conn = create_connection()
    create_table(conn)
    day = st.number_input('Enter the day', min_value=1)
    track_activities(conn, day)
    if st.button('Show activities'):
        activities = select_activities(conn, day)
        for activity in activities:
            st.write(activity)

if __name__ == "__main__":
    main()
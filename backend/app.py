from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, Float, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import date
from typing import List
from openai import OpenAI

app = FastAPI()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./activities.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ActivityDB(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    work = Column(Float)
    leisure = Column(Float)
    sleep = Column(Float)
    exercise = Column(Float)
    summary = Column(String)

Base.metadata.create_all(bind=engine)

class ActivityCreate(BaseModel):
    date: date
    work: float
    leisure: float
    sleep: float
    exercise: float

class Activity(ActivityCreate):
    id: int
    summary: str

    class Config:
        orm_mode = True

# Ollama setup
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama',
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_summary(activity: ActivityCreate) -> str:
    prompt = f"Analyze the following daily activity breakdown and provide a brief summary with insights and suggestions:\n"
    prompt += f"Date: {activity.date}\n"
    prompt += f"Work: {activity.work} hours\n"
    prompt += f"Leisure: {activity.leisure} hours\n"
    prompt += f"Sleep: {activity.sleep} hours\n"
    prompt += f"Exercise: {activity.exercise} hours\n"

    try:
        response = client.chat.completions.create(
            model="qwen2:7b",  # or any other model available in your Ollama setup
            messages=[
                {"role": "system", "content": "You are an AI assistant that provides insights on daily activities."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "Unable to generate summary at this time."

@app.post("/activities/", response_model=Activity)
def create_activity(activity: ActivityCreate, db: Session = Depends(get_db)):
    summary = generate_summary(activity)
    db_activity = ActivityDB(**activity.dict(), summary=summary)
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

@app.get("/activities/", response_model=List[Activity])
def read_activities(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    activities = db.query(ActivityDB).offset(skip).limit(limit).all()
    return activities

@app.get("/activities/{activity_id}", response_model=Activity)
def read_activity(activity_id: int, db: Session = Depends(get_db)):
    db_activity = db.query(ActivityDB).filter(ActivityDB.id == activity_id).first()
    if db_activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    return db_activity

@app.put("/activities/{activity_id}", response_model=Activity)
def update_activity(activity_id: int, activity: ActivityCreate, db: Session = Depends(get_db)):
    db_activity = db.query(ActivityDB).filter(ActivityDB.id == activity_id).first()
    if db_activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    for key, value in activity.dict().items():
        setattr(db_activity, key, value)
    
    db_activity.summary = generate_summary(activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

@app.delete("/activities/{activity_id}", response_model=Activity)
def delete_activity(activity_id: int, db: Session = Depends(get_db)):
    db_activity = db.query(ActivityDB).filter(ActivityDB.id == activity_id).first()
    if db_activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    db.delete(db_activity)
    db.commit()
    return db_activity

@app.post("/insights/")
def get_additional_insight(activity: ActivityCreate):
    prompt = f"Provide additional insights and recommendations based on this activity:\n"
    prompt += f"Date: {activity.date}\n"
    prompt += f"Work: {activity.work} hours\n"
    prompt += f"Leisure: {activity.leisure} hours\n"
    prompt += f"Sleep: {activity.sleep} hours\n"
    prompt += f"Exercise: {activity.exercise} hours\n"
    prompt += "Focus on long-term trends, health impacts, and productivity suggestions."

    try:
        response = client.chat.completions.create(
            model="qwen2:7b",
            messages=[
                {"role": "system", "content": "You are an AI assistant that provides in-depth insights on daily activities and habits."},
                {"role": "user", "content": prompt}
            ]
        )
        return {"insight": response.choices[0].message.content.strip()}
    except Exception as e:
        print(f"Error generating insight: {e}")
        return {"insight": "Unable to generate additional insight at this time."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# MongoDB Connection
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.school_activities
activities_collection = db.activities

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Initial activities data
initial_activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    # Sports related activities
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["alex@mergington.edu", "lucas@mergington.edu"]
    },
    "Basketball Club": {
        "description": "Practice basketball skills and play friendly games",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["mia@mergington.edu", "noah@mergington.edu"]
    },
    # Artistic activities
    "Art Workshop": {
        "description": "Explore painting, drawing, and sculpture techniques",
        "schedule": "Mondays, 4:00 PM - 5:30 PM",
        "max_participants": 18,
        "participants": ["ava@mergington.edu", "liam@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce school plays and performances",
        "schedule": "Fridays, 3:30 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "jack@mergington.edu"]
    },
    # Intellectual activities
    "Mathletes": {
        "description": "Compete in math competitions and solve challenging problems",
        "schedule": "Tuesdays, 4:00 PM - 5:00 PM",
        "max_participants": 10,
        "participants": ["ethan@mergington.edu", "grace@mergington.edu"]
    },
    "Science Club": {
        "description": "Conduct experiments and explore scientific concepts",
        "schedule": "Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 16,
        "participants": ["ben@mergington.edu", "zoe@mergington.edu"]
    }
}

@app.on_event("startup")
async def init_db():
    # Drop existing collection to start fresh
    await activities_collection.drop()
    # Insert all activities
    for name, details in initial_activities.items():
        await activities_collection.insert_one({"_id": name, **details})

@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
async def get_activities():
    cursor = activities_collection.find()
    activities = {}
    async for doc in cursor:
        name = doc.pop('_id')
        activities[name] = doc
    return activities

@app.post("/activities/{activity_name}/signup")
async def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Get the activity and validate it exists
    activity = await activities_collection.find_one({"_id": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student already signed up")
    
    # Add student
    result = await activities_collection.update_one(
        {"_id": activity_name},
        {"$push": {"participants": email}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to sign up student")
    
    return {"message": f"Signed up {email} for {activity_name}"}

# Endpoint to unregister a participant from an activity
@app.post("/activities/{activity_name}/unregister")
async def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Get the activity and validate it exists
    activity = await activities_collection.find_one({"_id": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Validate student is registered
    if email not in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student not registered for this activity")
    
    # Remove student
    result = await activities_collection.update_one(
        {"_id": activity_name},
        {"$pull": {"participants": email}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to remove student")
    
    return {"message": f"Removed {email} from {activity_name}"}

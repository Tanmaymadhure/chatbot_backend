from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware

from database import get_user, create_user
from models import SignupModel, LoginModel, ChatRequest
from auth import hash_password, verify_password, create_token, verify_token

import google.generativeai as genai


# ---------------------------
# Configure Gemini API
# ---------------------------
genai.configure(api_key="AIzaSyBmH8RPirUNqfVRWNLzCDw3Y1P-5xaZOGg")
model = genai.GenerativeModel("models/gemini-2.5-flash")


app = FastAPI()


# ---------------------------
# CORS Middleware
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------
# Helper: Validate JWT Token
# ---------------------------
def get_current_user(Authorization: str = Header(None)):
    if Authorization is None:
        raise HTTPException(401, "Missing Authorization header")

    token = Authorization.replace("Bearer ", "")
    decoded = verify_token(token)

    if decoded is None:
        raise HTTPException(401, "Invalid or expired token")

    return decoded



# -------------------------------------------------
# Signup Route
# -------------------------------------------------
@app.post("/signup")
def signup(user: SignupModel):
    existing = get_user(user.username)
    if existing:
        raise HTTPException(400, "User already exists")

    hashed_pw = hash_password(user.password)
    create_user(user.username, hashed_pw)

    return {"message": "User created successfully"}



# -------------------------------------------------
# Login Route
# -------------------------------------------------
@app.post("/login")
def login(user: LoginModel):
    db_user = get_user(user.username)

    if not db_user:
        raise HTTPException(400, "Invalid username")

    if not verify_password(user.password, db_user[2]):
        raise HTTPException(400, "Invalid password")

    token = create_token({"username": user.username})

    return {"message": "Login successful", "token": token}



# -------------------------------------------------
# Chat Route (JWT Protected)
# -------------------------------------------------
@app.post("/chat")
def chat(data: ChatRequest, current_user=Depends(get_current_user)):
    response = model.generate_content(data.prompt)
    answer = response.text

    return {"user": current_user["username"], "answer": answer}

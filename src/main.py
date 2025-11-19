from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from Database.database import get_db
from model.user import User
from Database.database import engine, Base
from schemas import SignupModel, LoginModel, ChatRequest
from Data_Redis.cache import memory
from auth import hash_password, verify_password, create_token, verify_token

from localmodel.ollama_model import ollama_llm

Base.metadata.create_all(bind=engine)

# genai.configure(api_key="AIzaSyBmH8RPirUNqfVRWNLzCDw3Y1P-5xaZOGg")
# model = genai.GenerativeModel("models/gemini-2.5-flash")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user(Authorization: str = Header(None)):
    if Authorization is None:
        raise HTTPException(401, "Missing Authorization header")
    token = Authorization.replace("Bearer ", "")
    decoded = verify_token(token)
    if decoded is None:
        raise HTTPException(401, "Invalid or expired token")
    return decoded




@app.post("/signup")
def signup(user: SignupModel, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(400, "User already exists")
    hashed_pw = hash_password(user.password)
    new_user = User(username=user.username, password=hashed_pw)
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully"}



@app.post("/login")
def login(user: LoginModel, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        raise HTTPException(400, "Invalid username")
    if not verify_password(user.password, db_user.password):
        raise HTTPException(400, "Invalid password")
    token = create_token({"username": user.username})
    return {"message": "Login successful", "token": token}



@app.post("/chat")
def chat(data: ChatRequest, current_user=Depends(get_current_user)):

    cached =memory.get(data.prompt)
    if cached:
        return {"user":current_user["username"], "answer": cached} 
    response = model.generate_content(data.prompt)
    memory.set(data.prompt,answer)
    return {"user": current_user["username"], "answer": response.text}




# @app.post("/chat/stream")
# async def chat_stream(data: ChatRequest, current_user=Depends(get_current_user)):
#     cached = memory.get(data.prompt)
#     if cached:
#         async def cached_stream():
#             print( cached) 
#             yield cached
#             yield "\n[DONE]"
#         return StreamingResponse(cached_stream(), media_type="text/plain")

#     async def generate():
#         stream = ollama_llm.astream(data.prompt)

#         full_answer = ""

#         async for token in stream:
           
#             text = token.content

#             full_answer += text
#             print( text)
#             yield text
       
     
#         memory.set(data.prompt, full_answer)

#         yield "\n[DONE]"

#     return StreamingResponse(generate(), media_type="text/plain")
@app.post("/chat/stream")
async def chat_stream(data: ChatRequest, current_user=Depends(get_current_user)):
    prompt = data.prompt

    cached = memory.get(prompt)
    if cached:
        async def cached_stream():
            print(cached, end="", flush=True)
            yield cached
            yield "\n[DONE]"
        return StreamingResponse(cached_stream(), media_type="text/plain")

    async def generate():
        stream = ollama_llm.astream(prompt)
        buffer = ""
        sentence_end = (".", "!", "?", "…")
        soft_end = (",", ";", ":", " ")

        async for chunk in stream:
            token = chunk.content
            buffer += token

            if token.endswith(sentence_end):
                print(buffer, end="", flush=True)
                yield buffer
                buffer = ""
                continue

            if token.endswith(soft_end) and len(buffer) > 12:
                print(buffer, end="", flush=True)
                yield buffer
                buffer = ""

        if buffer:
            print(buffer, end="", flush=True)
            yield buffer

        memory.set(prompt, buffer)

        print("\n")
        yield "\n[DONE]"

    return StreamingResponse(generate(), media_type="text/plain")

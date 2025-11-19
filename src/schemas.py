from pydantic import BaseModel

class SignupModel(BaseModel):
    username: str
    password: str

class LoginModel(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    prompt: str
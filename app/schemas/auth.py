from pydantic import BaseModel

class UserLogin(BaseModel):
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str  # username
    exp: int  # expiration timestamp 
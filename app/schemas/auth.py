from pydantic import BaseModel, validator

class UserLogin(BaseModel):
    username: str
    
    @validator('username')
    def username_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('username must not be empty')
        return v

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str  # username
    exp: int  # expiration timestamp 
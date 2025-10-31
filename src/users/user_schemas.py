from ninja import Schema

class CreateUser(Schema):
    """Schema to create a user"""
    username: str
    email: str
    password: str


class UserSchema(Schema):
    """Schema returned after user creation"""
    id: int
    username: str
    email: str

# backend/app/models.py
from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId
from pydantic.json_schema import JsonSchemaValue

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler) -> JsonSchemaValue:
        return {"type": "string"}

class UserModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    username: str
    hashed_password: str
    friends: Optional[List[str]] = []

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

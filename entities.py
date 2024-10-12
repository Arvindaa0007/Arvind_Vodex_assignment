from pydantic import BaseModel
from bson import ObjectId

class Item(BaseModel):
    name: str
    description: str
    price: float

class UserClockInRecord(BaseModel):
    user_id: str
    clock_in_time: str
    clock_out_time: str

# This can be used to convert ObjectId to str for response
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

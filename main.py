from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime
from typing import List, Optional, Dict, Any

app = FastAPI()

client = AsyncIOMotorClient("mongodb+srv://arvindaa0007:Arvind0007@cluster0.33urf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["Vodex_assignment"]

# Helper function to format item data from MongoDB for response
def item_helper(item) -> dict:
    return {
        "id": str(item["_id"]),  # Convert ObjectId to string
        "name": item["name"],  # String: User's name
        "email": item["email"],  # String: User's email
        "item_name": item["item_name"],  # String: Item name
        "quantity": item["quantity"],  # Integer: Quantity of the item
        "expiry_date": item["expiry_date"],  # String: Expiry date of the item (in ISO format)
        "insert_date": item["insert_date"]  # Datetime: Date when the item was inserted
    }

# Helper function to format clock-in data from MongoDB for response
def clock_in_helper(record) -> dict:
    return {
        "id": str(record["_id"]),  # Convert ObjectId to string
        "email": record["email"],  # String: User's email
        "location": record["location"],  # String: Location of clock-in
        "insert_datetime": record["insert_datetime"]  # Datetime: Date and time of clock-in
    }

# API endpoint to create a new item
@app.post("/items", response_model=dict)
async def create_item(item: Dict[str, Any]):
    # Expected fields for an item entity:
    # - name: string
    # - email: string
    # - item_name: string
    # - quantity: int
    # - expiry_date: string (ISO format)

    required_fields = ["name", "email", "item_name", "quantity", "expiry_date"]
    for field in required_fields:
        if field not in item:
            raise HTTPException(status_code=400, detail=f"{field} is required")

    # Insert date is automatically added
    insert_date = datetime.utcnow()
    new_item = {
        "name": item["name"],
        "email": item["email"],
        "item_name": item["item_name"],
        "quantity": item["quantity"],  # Integer value
        "expiry_date": item["expiry_date"],  # String: ISO format date
        "insert_date": insert_date  # Datetime: Current time in UTC
    }
    result = await db.items.insert_one(new_item)
    new_item["_id"] = result.inserted_id
    return item_helper(new_item)  # Return the newly inserted item as a dictionary

# API endpoint to retrieve an item by its ID
@app.get("/items/{id}", response_model=dict)
async def get_item(id: str):
    # The id parameter is a string representing the ObjectId
    item = await db.items.find_one({"_id": ObjectId(id)})
    if item is not None:
        return item_helper(item)  # Return the item data if found
    raise HTTPException(status_code=404, detail="Item not found")  # Return 404 if item doesn't exist

# API endpoint to filter items by multiple optional parameters
@app.get("/filter-items/filter", response_model=List[dict])
async def filter_items(
    email: Optional[str] = None,  # Optional string: filter by email
    expiry_date: Optional[str] = None,  # Optional string: filter by expiry date (ISO format)
    insert_date: Optional[str] = None,  # Optional string: filter by insert date (ISO format)
    quantity: Optional[int] = None  # Optional integer: filter by minimum quantity
):
    query = {}
    if email:
        query["email"] = email
    if expiry_date:
        query["expiry_date"] = {"$gt": datetime.fromisoformat(expiry_date)}  # Filter items with expiry date greater than provided
    if insert_date:
        query["insert_date"] = {"$gt": datetime.fromisoformat(insert_date)}  # Filter items inserted after the given date
    if quantity:
        query["quantity"] = {"$gte": quantity}  # Filter items with quantity greater than or equal to the given value
    
    items = await db.items.find(query).to_list(length=100)
    return [item_helper(item) for item in items]  # Return list of filtered items

# API endpoint to aggregate items by email and count occurrences
@app.get("/email-items/aggregate/email", response_model=List[dict])
async def aggregate_items_by_email():
    pipeline = [
        {"$group": {"_id": "$email", "count": {"$sum": 1}}}  # Group items by email and count occurrences
    ]
    results = await db.items.aggregate(pipeline).to_list(length=None)
    return [{"email": result["_id"], "count": result["count"]} for result in results]  # Return email and count for each user

# API endpoint to delete an item by its ID
@app.delete("/items/{id}", response_model=dict)
async def delete_item(id: str):
    # The id parameter is a string representing the ObjectId
    result = await db.items.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 1:
        return {"detail": "Item deleted"}  # Return success message if deletion is successful
    raise HTTPException(status_code=404, detail="Item not found")  # Return 404 if item doesn't exist

# API endpoint to update an item by its ID
@app.put("/items/{id}", response_model=dict)
async def update_item(id: str, item: Dict[str, Any]):
    # Fields that can be updated:
    # - name: string
    # - email: string
    # - item_name: string
    # - quantity: int
    # - expiry_date: string (ISO format)
    update_data = {k: v for k, v in item.items() if k in ["name", "email", "item_name", "quantity", "expiry_date"]}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields provided for update")

    result = await db.items.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    if result.modified_count == 1:
        updated_item = await db.items.find_one({"_id": ObjectId(id)})
        return item_helper(updated_item)  # Return the updated item data
    raise HTTPException(status_code=404, detail="Item not found")  # Return 404 if item doesn't exist

# API endpoint to create a new clock-in record
@app.post("/clock-in", response_model=dict)
async def create_clock_in(record: Dict[str, Any]):
    # Expected fields for a clock-in entity:
    # - email: string
    # - location: string
    required_fields = ["email", "location"]
    for field in required_fields:
        if field not in record:
            raise HTTPException(status_code=400, detail=f"{field} is required")

    insert_datetime = datetime.utcnow()  # Insert current date and time (UTC)
    new_record = {
        "email": record["email"],  # String: User's email
        "location": record["location"],  # String: Location of the clock-in
        "insert_datetime": insert_datetime  # Datetime: Current date and time
    }
    result = await db.clockin.insert_one(new_record)
    new_record["_id"] = result.inserted_id
    return clock_in_helper(new_record)  # Return the newly created clock-in record

# API endpoint to retrieve a clock-in record by its ID
@app.get("/clock-in/{id}", response_model=dict)
async def get_clock_in(id: str):
    # The id parameter is a string representing the ObjectId
    record = await db.clockin.find_one({"_id": ObjectId(id)})
    if record is not None:
        return clock_in_helper(record)  # Return the clock-in record if found
    raise HTTPException(status_code=404, detail="Record not found")  # Return 404 if record doesn't exist

# API endpoint to filter clock-in records by optional parameters
@app.get("/clock-in-filter/filter", response_model=List[dict])
async def filter_clock_in(
    email: Optional[str] = None,  # Optional string: filter by email
    location: Optional[str] = None,  # Optional string: filter by location
    insert_datetime: Optional[str] = None  # Optional string: filter by clock-in date (ISO format)
):
    query = {}
    if email:
        query["email"] = email
    if location:
        query["location"] = location
    if insert_datetime:
        query["insert_datetime"] = {"$gt": datetime.fromisoformat(insert_datetime)}  # Filter by clock-in date greater than provided
    
    records = await db.clockin.find(query).to_list(length=100)
    return [clock_in_helper(record) for record in records]  # Return list of filtered clock-in records

# API endpoint to delete a clock-in record by its ID
@app.delete("/clock-in/{id}", response_model=dict)
async def delete_clock_in(id: str):
    # The id parameter is a string representing the ObjectId
    result = await db.clockin.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 1:
        return {"detail": "Clock-in record deleted"}  # Return success message if deletion is successful
    raise HTTPException(status_code=404, detail="Record not found")  # Return 404 if record doesn't exist

# API endpoint to update a clock-in record by its ID
@app.put("/Clock-in-update/{id}", response_model=dict)
async def update_clock_in(id: str, record: Dict[str, Any]):
    # Fields that can be updated:
    # - email: string
    # - location: string
    update_data = {k: v for k, v in record.items() if k in ["email", "location"]}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields provided for update")

    result = await db.clockin.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    if result.modified_count == 1:
        updated_record = await db.clockin.find_one({"_id": ObjectId(id)})
        return clock_in_helper(updated_record)  # Return the updated clock-in record
    raise HTTPException(status_code=404, detail="Record not found")  # Return 404 if record doesn't exist













# backend/app/routes/friends.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..utils.auth import get_current_user
from ..database import db

router = APIRouter(prefix="/friends", tags=["friends"])

class FriendAddRequest(BaseModel):
    username: str

@router.get("/search")
async def search_users(query: str, current_user: dict = Depends(get_current_user)):
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    cursor = db.users.find({
        "username": {"$regex": f"^{query}", "$options": "i"},
        "username": {"$ne": current_user["username"]}
    }, {"username": 1})

    results = []
    async for user in cursor:
        results.append(user["username"])

    return {"results": results}


@router.post("/add")
async def add_friend(request: FriendAddRequest, current_user: dict = Depends(get_current_user)):
    username = request.username

    if username == current_user["username"]:
        raise HTTPException(status_code=400, detail="You cannot add yourself")

    friend_user = await db.users.find_one({"username": username})
    if not friend_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already friends
    current_user_data = await db.users.find_one({"username": current_user["username"]})
    if current_user_data and "friends" in current_user_data and username in current_user_data["friends"]:
        return {"msg": "Already friends"}

    await db.users.update_one(
        {"username": current_user["username"]},
        {"$addToSet": {"friends": username}}
    )

    await db.users.update_one(
        {"username": username},
        {"$addToSet": {"friends": current_user["username"]}}
    )

    return {"msg": f"{username} added as a friend"}

@router.get("/list")
async def friend_list(current_user: dict = Depends(get_current_user)):
    user_data = await db.users.find_one({"username": current_user["username"]})
    if not user_data:
        return {"friends": []}

    friends = user_data.get("friends", [])
    return {"friends": friends}

# Optional for testing: list all users
@router.get("/all")
async def list_all_users(current_user: dict = Depends(get_current_user)):
    cursor = db.users.find({}, {"username": 1})
    users = []
    async for user in cursor:
        users.append(user["username"])
    return {"users": users}


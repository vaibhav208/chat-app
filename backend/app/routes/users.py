from fastapi import APIRouter, Depends, HTTPException, Query, Body
from ..database import db
from ..utils.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/search")
async def search_users(username: str = Query(...), current_user: dict = Depends(get_current_user)):
    user = current_user["username"]

    # Find users with matching username, exclude self
    cursor = db.users.find({
        "username": {"$regex": f"^{username}", "$options": "i"},
        "username": {"$ne": user}
    })

    results = []
    async for doc in cursor:
        results.append(doc["username"])

    return {"results": results}

@router.post("/add-friend")
async def add_friend(friend_username: str = Body(...), current_user: dict = Depends(get_current_user)):
    user = current_user["username"]

    if friend_username == user:
        raise HTTPException(status_code=400, detail="Cannot add yourself as a friend")

    # Check if friend exists
    friend = await db.users.find_one({"username": friend_username})
    if not friend:
        raise HTTPException(status_code=404, detail="User to add not found")

    # Add friend_username to user's friend list if not already present
    await db.users.update_one(
        {"username": user, "friends": {"$ne": friend_username}},  # friends field is an array
        {"$push": {"friends": friend_username}}
    )

    # Optionally, add user to friend's friend list for mutual friendship
    await db.users.update_one(
        {"username": friend_username, "friends": {"$ne": user}},
        {"$push": {"friends": user}}
    )

    return {"msg": f"{friend_username} added as friend"}
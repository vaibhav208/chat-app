# backend/app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware  # ✅ Import CORS
from .database import db
from .utils.auth import get_current_user
from .routes import auth, friends, chat, ws_chat, users

app = FastAPI()

# ✅ Add CORS middleware to allow frontend (http://localhost:3000) to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # allow all methods like GET, POST, etc.
    allow_headers=["*"],  # allow all headers
)

# ✅ Include routers
app.include_router(auth.router)
app.include_router(friends.router)
app.include_router(chat.router)
app.include_router(ws_chat.router)
app.include_router(users.router)

# ✅ Test route
@app.get("/")
async def root():
    collections = await db.list_collection_names()
    return {"collections": collections}

# ✅ Protected route to get current user
@app.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}

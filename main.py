print("Importing modules...")

from pathlib import Path
from pydantic import BaseModel
import uvicorn
from fastapi import FastAPI, Response, Cookie, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import sqlite3
import hashlib
import uuid

Path("uploads").mkdir(parents=True, exist_ok=True)

# ==== Some settings ====

print("Setting some settings variables...")

instanceMotd = "vadim gay"
instanceMascotImage = "" # Leave empty is your instance doesn't have mascot image
instanceMascotName = "" # Leave empty is your instance doesn't have mascot at all
backendPort = 8000
hostingLocally = True
api_path = "" # This is where you put the api path (example: https://example.social/[api_path variable]/[endpoints]) (if api is not on separate (sub)domain, please put "/" at the beginning please)
testMode = True
CORSorigins = ["*"]

# ==== Database ====

print("Initializing DB...")

conn = sqlite3.connect("KagamiHiiragi.db", check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            userid INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            login TEXT NOT NULL,
            password TEXT NOT NULL,
            reg_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            username TEXT NOT NULL,
            firstname TEXT NOT NULL,
            lastname TEXT,
            nickname TEXT,
            avatar TEXT,
            bio TEXT,
            contacts TEXT,
            favfilms TEXT,
            favmusic TEXT,
            favgames TEXT,
            additionalinfo TEXT
        )
    ''') # мотя сказал что лучше сделать чтобы в этой таблице были логины пароли вместе с отображаемыми данными, типо имя и фамилия, мне лично это не нравиться, но делаю как сказал мотя -дреля
    # Passwords are hashed using MD5 since this is just a hobby project
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS friends (
            useridfollower INTEGER NOT NULL,
            useridfollowing INTEGER NOT NULL,
            areFriends INTERGER NOT NULL DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            userid INTEGER NOT NULL,
            posttext TEXT NOT NULL,
            attachedimage TEXT,
            repostpostid INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            uuidsession TEXT NOT NULL,
            userid INTEGER NOT NULL
        )
    ''')
    conn.commit()

init_db() # telling server to shit itself

# ==== FastAPI stuff duh ====

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORSorigins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==== Classes ====

class loginData(BaseModel):
    login: str
    passwordmd5: str

class regData(BaseModel):
    login: str
    passwordmd5: str
    username: str
    firstname: str
    lastname: Optional[str] = None
    nickname: Optional[str] = None

# ==== API endpoints ====

@app.get(f"{api_path}/") # It is returning some instance info, but most of instance info is stored in "kagamiumInstance.js" file in frontend part of this project
async def root():
    return {"motd": instanceMotd, "mascotName": instanceMascotName, "mascotImage": instanceMascotImage}

# ==== Authorization system ====

@app.get(f"{api_path}/login") # Had to vibecode this, same strings for some reason are not the same, wtf???
async def login_process(response: Response, data: loginData):
    cursor.execute("SELECT userid, password FROM users WHERE login = ?", (data.login,))
    user_data = cursor.fetchone()
    if not user_data:
        return {"status": "failed"}
    user_id, db_password_hash = user_data
    if db_password_hash == data.passwordmd5:
        sessionuuid = str(uuid.uuid4())
        cursor.execute("INSERT INTO sessions (uuidsession, userid) VALUES (?, ?)", (sessionuuid, user_id))
        conn.commit()
        response.set_cookie(key="uuidsession", value=sessionuuid)
        if testMode == True: return {"sessionuuid": sessionuuid}
        else: return {"status": "success"}
    else:
        return {"status": "failed"}

@app.post(f"{api_path}/register")
async def register_process(response: Response, data: regData):
    cursor.execute("SELECT login FROM users WHERE login = ?", (data.login,))
    loginexists = cursor.fetchone()
    if loginexists is None:
        cursor.execute("INSERT INTO users (login, password, username, firstname, lastname, nickname) VALUES (?, ?, ?, ?, ?, ?)", (data.login, data.passwordmd5, data.username, data.firstname, data.lastname, data.nickname))
        conn.commit()
        cursor.execute("SELECT userid FROM users WHERE login = ?", (data.login,))
        userid = cursor.fetchone()
        sessionuuid = str(uuid.uuid4())
        cursor.execute("INSERT INTO sessions (uuidsession, userid) VALUES (?, ?)", (sessionuuid, userid[0]))
        conn.commit()
        response.set_cookie(key="uuidsession", value=sessionuuid)
        if testMode == True: return {"sessionuuid": sessionuuid}
        else: return {"status": "success"}
    else:
        return {"status": "failed"}

@app.get("/logout")
async def logout(response: Response):
    response.set_cookie(key="uuidsession", value="null") # I know this is stupid
    response.delete_cookie(key="sessionuuid") # ts don't work man, but I'll leave it there just in case
    return {"status": "success"}
        
# ==== Some Profile APIs ====

@app.get(f"{api_path}/profile")
async def give_profile_info(uuidsession: Optional[str] = Cookie(None), id: Optional[str] = None):
    if id is None:
        if uuidsession is not None and uuidsession != "null":
            userid = getUserIDfromSessionUUID(uuidsession)
            cursor.execute("SELECT reg_date, username, firstname, lastname, nickname, avatar, bio, contacts, favfilms, favmusic, favgames, additionalinfo FROM users WHERE userid = ?", (userid,))
            profileData = cursor.fetchone()
            reg_date, username, firstname, lastname, nickname, avatar, bio, contacts, favfilms, favmusic, favgames, additionalinfo = profileData
            return {"id": userid, "username": username, "firstname": firstname, "lastname": lastname, "nickname": nickname, "reg_date": reg_date, "avatar": avatar, "bio": bio, "contacts": contacts, "favfilms": favfilms, "favmusic": favmusic, "favgames": favgames, "additionalinfo": additionalinfo}
        else: return {"status": "failed", "details": "User ID is not specified"}
    else:
        cursor.execute("SELECT reg_date, username, firstname, lastname, nickname, avatar, bio, contacts, favfilms, favmusic, favgames, additionalinfo FROM users WHERE userid = ?", (id,))
        profileData = cursor.fetchone()
        reg_date, username, firstname, lastname, nickname, avatar, bio, contacts, favfilms, favmusic, favgames, additionalinfo = profileData
        return {"id": id, "username": username, "firstname": firstname, "lastname": lastname, "nickname": nickname, "reg_date": reg_date, "avatar": avatar, "bio": bio, "contacts": contacts, "favfilms": favfilms, "favmusic": favmusic, "favgames": favgames, "additionalinfo": additionalinfo}

@app.get(f"{api_path}/profile/follow") # I had to vibecode this, my code was so fucked up that... I just fucking gave up
async def follow_profile(uuidsession: Optional[str] = Cookie(None), *, id: int): # also about that... you can follow and friend yourself! Bcuz OpenVK can do that too! This won't be fixed. FRIEND YOURSELF!!!!
    if uuidsession is None and uuidsession == "null":
        return {"status": "failed", "details": "Authorization required"}
    userid = getUserIDfromSessionUUID(uuidsession)
    cursor.execute("SELECT userid FROM users WHERE userid = ?", (id,))
    if cursor.fetchone() is None:
        return {"status": "failed", "details": "User does not exist"}
    cursor.execute("SELECT areFriends FROM friends WHERE useridfollower = ? AND useridfollowing = ?", (userid, id))
    forward_follow = cursor.fetchone()
    if forward_follow:
        cursor.execute("UPDATE friends SET areFriends = 1 WHERE useridfollower = ? AND useridfollowing = ?", (userid, id))
        conn.commit()
        return {"status": "success", "details": "Friends"}
    cursor.execute("SELECT areFriends FROM friends WHERE useridfollower = ? AND useridfollowing = ?", (id, userid))
    backward_follow = cursor.fetchone()
    if backward_follow:
        cursor.execute("UPDATE friends SET areFriends = 1 WHERE useridfollower = ? AND useridfollowing = ?", (id, userid))
        cursor.execute("INSERT OR IGNORE INTO friends (useridfollower, useridfollowing, areFriends) VALUES (?, ?, 1)", (userid, id))
        conn.commit()
        return {"status": "success", "details": "Friends"}
    else:
        cursor.execute("INSERT INTO friends (useridfollower, useridfollowing, areFriends) VALUES (?, ?, 0)", (userid, id))
        conn.commit()
        return {"status": "success"}

# ==== Test mode API endpoints ====

@app.get(f"{api_path}/sessionuuid")
async def get_cookie(uuidsession: Optional[str] = Cookie(None)):
    if testMode == True:
        return {"sessionuuid": uuidsession}
    else: return {"status": "failed", "details": "Kagamium instance in production mode"}

@app.get(f"{api_path}/setsessionuuid")
async def set_cookie(response: Response, uuid: str):
    if testMode == True:
        sessionexists = getUserIDfromSessionUUID(uuid)
        if sessionexists is not None:
            response.set_cookie(key="uuidsession", value=uuid)
            return {"status": "success"}
        else: return {"status": "failed"}
    else: return {"status": "failed", "details": "Kagamium instance in production mode"}

# ==== Defines ====

def getUserIDfromSessionUUID(uuidsession):
    cursor.execute("SELECT userid FROM sessions WHERE uuidsession = ?", (uuidsession,))
    return cursor.fetchone()[0]

# ==== The part where server starts ====

print("Starting server!")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1" if hostingLocally is True else "0.0.0.0", port=backendPort)
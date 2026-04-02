print("Importing modules...")

from pydantic import BaseModel
import uvicorn
from fastapi import FastAPI, Response, Cookie, Header
from typing import Optional
import sqlite3
import hashlib
import uuid

# ==== Some settings ====

print("Setting some settings variables...")

backendPort = 8000
hostingLocally = True
api_path = "" # This is where you put the api path (example: https://example.social/[api_path variable]/[endpoints]) (if api is not on separate (sub)domain, please put "/" at the beginning please)

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
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            userid INTEGER NOT NULL,
            posttext TEXT NOT NULL,
            attachedimagefilename TEXT,
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

app = FastAPI()

# ==== Classes ====

class loginData(BaseModel):
    login: str
    passwordmd5: str

class regData(BaseModel):
    login: str
    password: str
    username: str
    firstname: str
    lastname: Optional[str] = None
    nickname: Optional[str] = None

# ==== API Endpoints ====

@app.get(f"{api_path}/") # It would have return the instance info, but instance info is stored in "kagamiumInstance.js" file in frontend part of this project
async def root():
    return {"message": "Konata Izumi"} # посхалко 1488

# ==== Logging/registering process ====

@app.get(f"{api_path}/login")
async def login_process(response: Response, data: loginData):
    try:
        cursor.execute("SELECT userid, password FROM users WHERE login = ?", (data.login,))
        user_data = cursor.fetchone()
        if not user_data:
            return {"status": "failed"}
        user_id, db_password_hash = user_data
        if db_password_hash == data.passwordmd5:
            session_id = str(uuid.uuid4())
            cursor.execute("INSERT INTO sessions (uuidsession, userid) VALUES (?, ?)", (session_id, user_id))
            conn.commit()
            response.set_cookie(key="uuidsession", value=session_id)
            return {"status": "success"}
        else:
            return {"status": "failed"}

    except Exception as e:
        print(f"server shat itself: {e}") 
        return {"status": "error"}

@app.post(f"{api_path}/register")
async def register_process(response: Response, data: regData):
    try:
        cursor.execute("SELECT login FROM users WHERE login = ?", (data.login,))
        loginexists = cursor.fetchone()
        if loginexists is None:
            passwordhash = hashlib.md5(data.password.encode('utf-8')).hexdigest()
            cursor.execute("INSERT INTO users (login, password, username, firstname, lastname, nickname) VALUES (?, ?, ?, ?, ?, ?)", (data.login, passwordhash, data.username, data.firstname, data.lastname, data.nickname))
            conn.commit()
            cursor.execute("SELECT userid FROM users WHERE login = ?", (data.login,))
            userid = cursor.fetchone()
            session_id = str(uuid.uuid4())
            cursor.execute("INSERT INTO sessions (uuidsession, userid) VALUES (?, ?)", (session_id, userid[0]))
            conn.commit()
            response.set_cookie(key="uuidsession", value=session_id)
            return {"status": "success"}
        else:
            return {"status": "failed"}

    except Exception as e:
        print(f"server shat itself: {e}") 
        return {"status": "error"}
        
@app.get(f"{api_path}/sessionuuid")
async def get_cookie(uuidsession: Optional[str] = Cookie(None)):
    return {"sessionuuid": uuidsession}

# ==== The part where server starts ====

print("Starting server!")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1" if hostingLocally is True else "0.0.0.0", port=backendPort)
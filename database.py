# yes this have one function but i hope we'll move here all database intesractions soon

import sqlite3
import os

def file(target): # stupid but why not
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), target)

conn = sqlite3.connect(file("KagamiHiiragi.db"), check_same_thread=False)
cursor = conn.cursor()



def init():
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
    # ну и пидорас же этот ваш мотя блин -мотя
    # Passwords are hashed using MD5 since this is just a hobby project штоооооо ну ладна
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
    return
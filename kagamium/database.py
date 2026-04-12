from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from threading import RLock


@dataclass(slots=True)
class UserProfile:
    user_id: int
    reg_date: str
    username: str
    firstname: str
    lastname: str | None
    nickname: str | None
    avatar: str | None
    bio: str | None
    contacts: str | None
    favfilms: str | None
    favmusic: str | None
    favgames: str | None
    additionalinfo: str | None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> UserProfile:
        return cls(
            user_id=row["userid"],
            reg_date=row["reg_date"],
            username=row["username"],
            firstname=row["firstname"],
            lastname=row["lastname"],
            nickname=row["nickname"],
            avatar=row["avatar"],
            bio=row["bio"],
            contacts=row["contacts"],
            favfilms=row["favfilms"],
            favmusic=row["favmusic"],
            favgames=row["favgames"],
            additionalinfo=row["additionalinfo"],
        )

    def as_response(self) -> dict[str, int | str | None]:
        return {
            "id": self.user_id,
            "username": self.username,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "nickname": self.nickname,
            "reg_date": self.reg_date,
            "avatar": self.avatar,
            "bio": self.bio,
            "contacts": self.contacts,
            "favfilms": self.favfilms,
            "favmusic": self.favmusic,
            "favgames": self.favgames,
            "additionalinfo": self.additionalinfo,
        }


class Database:
    def __init__(self, database_path: Path) -> None:
        self._lock = RLock()
        self._connection = sqlite3.connect(str(database_path), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row

    @contextmanager
    def _cursor(self, *, commit: bool = False) -> Iterator[sqlite3.Cursor]:
        with self._lock:
            cursor = self._connection.cursor()
            try:
                yield cursor
                if commit:
                    self._connection.commit()
            finally:
                cursor.close()

    def initialize(self) -> None:
        statements = (
            """
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
            """,
            """
            CREATE TABLE IF NOT EXISTS friends (
                useridfollower INTEGER NOT NULL,
                useridfollowing INTEGER NOT NULL,
                areFriends INTERGER NOT NULL DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                userid INTEGER NOT NULL,
                posttext TEXT NOT NULL,
                attachedimage TEXT,
                repostpostid INTEGER
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_users_login ON users (login)",
            (
                "CREATE INDEX IF NOT EXISTS idx_friends_pair "
                "ON friends (useridfollower, useridfollowing)"
            ),
        )

        with self._cursor(commit=True) as cursor:
            for statement in statements:
                cursor.execute(statement)

    def get_user_credentials(self, login: str) -> tuple[int, str] | None:
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT userid, password FROM users WHERE login = ?",
                (login,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return int(row["userid"]), str(row["password"])

    def login_exists(self, login: str) -> bool:
        with self._cursor() as cursor:
            cursor.execute("SELECT 1 FROM users WHERE login = ?", (login,))
            return cursor.fetchone() is not None

    def create_user(
        self,
        *,
        login: str,
        password_hash: str,
        username: str,
        firstname: str,
        lastname: str | None = None,
        nickname: str | None = None,
    ) -> int:
        with self._cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO users (
                    login,
                    password,
                    username,
                    firstname,
                    lastname,
                    nickname
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    login,
                    password_hash,
                    username,
                    firstname,
                    lastname,
                    nickname,
                ),
            )
            return int(cursor.lastrowid)

    def update_user_password(self, user_id: int, password_hash: str) -> None:
        with self._cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE users SET password = ? WHERE userid = ?",
                (password_hash, user_id),
            )

    def get_profile(self, user_id: int) -> UserProfile | None:
        with self._cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    userid,
                    reg_date,
                    username,
                    firstname,
                    lastname,
                    nickname,
                    avatar,
                    bio,
                    contacts,
                    favfilms,
                    favmusic,
                    favgames,
                    additionalinfo
                FROM users
                WHERE userid = ?
                """,
                (user_id,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return UserProfile.from_row(row)

    def user_exists(self, user_id: int) -> bool:
        with self._cursor() as cursor:
            cursor.execute("SELECT 1 FROM users WHERE userid = ?", (user_id,))
            return cursor.fetchone() is not None

    def follow_user(self, follower_id: int, following_id: int) -> str | None:
        with self._cursor(commit=True) as cursor:
            cursor.execute(
                """
                SELECT areFriends
                FROM friends
                WHERE useridfollower = ? AND useridfollowing = ?
                """,
                (follower_id, following_id),
            )
            forward_follow = cursor.fetchone()
            if forward_follow is not None:
                cursor.execute(
                    """
                    UPDATE friends
                    SET areFriends = 1
                    WHERE useridfollower = ? AND useridfollowing = ?
                    """,
                    (follower_id, following_id),
                )
                return "Friends"

            cursor.execute(
                """
                SELECT areFriends
                FROM friends
                WHERE useridfollower = ? AND useridfollowing = ?
                """,
                (following_id, follower_id),
            )
            backward_follow = cursor.fetchone()
            if backward_follow is not None:
                cursor.execute(
                    """
                    UPDATE friends
                    SET areFriends = 1
                    WHERE useridfollower = ? AND useridfollowing = ?
                    """,
                    (following_id, follower_id),
                )
                cursor.execute(
                    """
                    INSERT INTO friends (useridfollower, useridfollowing, areFriends)
                    VALUES (?, ?, 1)
                    """,
                    (follower_id, following_id),
                )
                return "Friends"

            cursor.execute(
                """
                INSERT INTO friends (useridfollower, useridfollowing, areFriends)
                VALUES (?, ?, 0)
                """,
                (follower_id, following_id),
            )

        return None

from datetime import datetime

import aiosql
import aiosqlite
from aiosqlite import Connection
from pydantic import BaseModel

DB_FILE = "sharednotes.db"
SQL_FILE = "sharednotes.sql"

queries = aiosql.from_path(SQL_FILE, "aiosqlite")


class Note(BaseModel):
    title: str
    content: str

    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        schema_extra = {
            "example": {
                "title": "My First Note",
                "content": "This is my first note. It's pretty cool.",
                "created_at": "2023-02-18T12:00:00Z",
                "updated_at": "2023-02-18T18:30:00Z",
            }
        }

        json_encoders = {
            datetime: lambda dt: dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
        }


class NoteInDb(Note):
    created_at: datetime
    updated_at: datetime


class NoteDAO:
    @staticmethod
    async def get_db_conn():
        """
        Get a connection to the database.
        """
        conn = await aiosqlite.connect(DB_FILE)
        conn.row_factory = aiosqlite.Row

        await queries.create_tables(conn)
        await queries.create_triggers(conn)

        try:
            yield conn
        finally:
            await conn.close()

    @staticmethod
    async def get(conn: Connection, title: str) -> NoteInDb | None:
        """
        Get a note by title.
        """
        result = await queries.get_note(conn, title=title)
        if result is None:
            return None
        return NoteInDb.parse_obj(result)

    @staticmethod
    async def put(conn: Connection, title: str, content: str,
                  version: int) -> NoteInDb | None:
        """
        Put (upsert: update or insert) a note.
        """
        await queries.put_note(conn, title=title, content=content,
                               updated_at=version)
        await conn.commit()

        result = await queries.get_note(conn, title=title, content=content)
        if result is None:
            raise Exception("Note not found after upsert")
        return NoteInDb.parse_obj(result)

    @staticmethod
    async def delete(conn: Connection, title: str) -> int:
        """
        Delete a note.
        """
        num_deleted = queries.delete_note(conn, title=title)
        await conn.commit()
        return num_deleted

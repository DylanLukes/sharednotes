from datetime import datetime
from sqlite3 import IntegrityError
from typing import Optional

from aiosqlite import Connection
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

from database import NoteDAO, Note

app = FastAPI(title="Shared Notes", description="A simple shared notes API.", version="0.2.0")


class LocationPut(BaseModel):
    content: str
    version: Optional[int] = 0

    class Config:
        schema_extra = {
            "example": {
                "content": "This is a note.",
                "version": 0
            }
        }


@app.get("/echo/{message}")
async def echo(message: str):
    return {"message": message}


@app.get("/notes/{title}", response_model=Note, response_model_exclude_unset=True)
async def get_note(title: str, conn: Connection = Depends(NoteDAO.get_db_conn)):
    note = await NoteDAO.get(conn, title)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")
    return note


@app.put("/notes/{title}",
         response_model=Note,
         response_model_exclude_unset=True)
async def put_note(
        title: str,
        request: LocationPut,
        conn: Connection = Depends(NoteDAO.get_db_conn),
):
    try:
        note = await NoteDAO.put(conn, title, request.content, request.version)
    except IntegrityError as e:
        if "older" in str(e):
            raise HTTPException(status_code=409,
                                detail="Rejected for conflict: server has newer "
                                       "version of this note.")
        else:
            raise HTTPException(status_code=500, detail="Database error.")
    return note


# @app.delete("/notes/{title}")
# async def delete_note(
#         title: str,
#         conn: Connection = Depends(NoteDAO.get_db_conn),
# ):
#     try:
#         await NoteDAO.delete(conn, title)
#     except IntegrityError as e:
#         raise HTTPException(status_code=500, detail="Database error.")
#     return {"message": "Note deleted."}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

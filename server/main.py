import datetime
import sqlite3
import os
from pathlib import Path
from typing import TYPE_CHECKING

import uvicorn
from fastapi import FastAPI, HTTPException, Form

if TYPE_CHECKING:
    from starlette.datastructures import State

sqlite3.row_factory = sqlite3.Row  
# This is needed to make the rows behave like dictionaries,
# which is easier to work with.


# Instantiate the FastAPI app
app = FastAPI(
    debug=True,
    title="Nex late tracker - API",
    description="The API for the nex late tracker example.",
    root_path="/api"  # comment this out if you're not running behind the reverse proxy
)
if TYPE_CHECKING:
    # noinspection PyTypeHints
    app.state: "State"
# Create the database connection.
# this should be set in app.state to avoid creating a new connection for each request
# Also, if you don't put it in app.state, you may get threading errors.
DB_DIR = os.getenv("DB_DIR", "./")
DB_LOC = Path(DB_DIR) / "nex_late_tracker.db"
app.state.db = sqlite3.connect(str(DB_LOC.absolute()), check_same_thread=False)


class Cursor:
    """A context manager that automatically commits and closes the cursor."""
    # This isn't really needed but it's handy
    def __init__(self, db: sqlite3.Connection = app.state.db):
        self.db = db

    def __enter__(self):
        self.cursor = self.db.cursor()
        self.cursor.row_factory = sqlite3.Row
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.commit()
        self.cursor.close()


# Create the table
app.state.db.execute(
    """
    CREATE TABLE IF NOT EXISTS lates (
        date TEXT NOT NULL PRIMARY KEY,
        minutes_late INTEGER NOT NULL,
        excuse TEXT DEFAULT NULL
    );
    """
)


@app.get("/lates/all")
def get_lates(limit: int = -1, newest_first: bool = True):
    # `limit` here becomes a query parameter (i.e. /lates/all?limit=10)
    """Fetches ALL late entries."""
    parsed = {}  # this will become a dictionary of {string: data}
    with Cursor() as cursor:
        cursor.execute("SELECT date, minutes_late, excuse FROM lates LIMIT ?", (limit,))
        # This makes the cursor execute that. The `?` is a placeholder for the limit parameter.
        # Translated, this executes `SELECT date, minutes_late, excuse FROM lates LIMIT 10`
        for row in cursor.fetchall():
            # This makes it so that the row is a dictionary, which is easier to work with.
            parsed[row["date"]] = {
                "minutes_late": row["minutes_late"],
                "excuse": row["excuse"]
            }
    if newest_first:
        parsed = dict(reversed(list(parsed.items())))
    return parsed  # returns the dictionary as JSON with response code 200 by default.


@app.get("/lates/{year}/{month}/{day}")
def get_late(year: int, month: int, day: int):  # These are path parameters (i.e. /lates/2023/1/2)
    """Fetches a specific late entry."""
    with Cursor() as cursor:
        cursor.execute(
            "SELECT date, minutes_late, excuse FROM lates WHERE date = ?",
            (f"{day}/{month}/{year}",)
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(  # properly returns a 404 error, body being {"detail": "That entry does not exist."}
                status_code=404,
                detail="That entry does not exist."
            )
        return {
            "date": row["date"],
            "minutes_late": row["minutes_late"],
            "excuse": row["excuse"]
        }


@app.post("/lates")  # This is a POST request, which is used to create new entries.
def post_late(minutes_late: int = Form(...), excuse: str = Form(None)):
    """Creates a new late entry"""
    now = datetime.datetime.now()
    day, month, year = map(int, now.strftime("%d/%m/%Y").split("/"))
    cursor = Cursor()

    # Both `minutes_late` and `excuse` are in the form body, not URL.
    # `minutes_late` is required, `excuse` is optional.
    # First we need to make sure there isn't already an entry for today.
    with Cursor() as cursor:
        cursor.execute("SELECT date FROM lates WHERE date = ?", (f"{day}/{month}/{year}",))
        if cursor.fetchone() is not None:
            raise HTTPException(
                status_code=400,
                detail="There is already an entry for today. Did you mean to edit it (PUT)?"
            )
        # If there isn't, we can create the entry.
        cursor.execute(
            "INSERT INTO lates (date, minutes_late, excuse) VALUES (?, ?, ?)",
            (
                f"{day}/{month}/{year}",
                minutes_late,
                excuse
            )
        )
        app.state.db.commit()  # This is needed to save the changes to the database.
    return {
        "date": f"{day}/{month}/{year}",
        "minutes_late": minutes_late,
        "excuse": excuse
    }


@app.put("/lates/{year}/{month}/{day}")
def put_late(year: int, month: int, day: int, minutes_late: int = Form(None), excuse: str = Form(None)):
    """Edits an existing late entry.

    You are unable to edit the date of an entry, however both minutes and excuse can be.
    If you don't want to edit one of the fields, just don't include it in the request body.
    """
    with Cursor() as cursor:
        cursor.execute("SELECT (date, minutes_late, excuse) FROM lates WHERE date = ?", (f"{day}/{month}/{year}",))
        existing_row = cursor.fetchone()
        if existing_row is None:
            raise HTTPException(
                status_code=404,
                detail="That entry does not exist."
            )

        # First, we need to delete the entry
        cursor.execute(
            "DELETE FROM lates WHERE date = ?",
            (f"{day}/{month}/{year}",)
        )
        # Then, we need to create a new entry with the same date, but with the new values.
        args = [f"{day}/{month}/{year}"]
        if minutes_late is not None:
            args.append(minutes_late)
        else:
            args.append(existing_row["minutes_late"])
        if excuse is not None:
            args.append(excuse)
        else:
            args.append(existing_row["excuse"])

        cursor.execute(
            "INSERT INTO lates (date, minutes_late, excuse) VALUES (?, ?, ?)",
            tuple(args)
        )
        # and commit the changes to the database.
        # Remember, this is one big transaction - if we fail before now, the server will raise HTTP 500,
        # And the changes to the database won't be saved.
        app.state.db.commit()
    return {
        "date": f"{day}/{month}/{year}",
        "minutes_late": args[1],
        "excuse": args[2]
    }


@app.delete("/lates/{year}/{month}/{day}")
def delete_late(year: int, month: int, day: int):
    """Deletes an existing late entry."""
    with Cursor() as cursor:
        cursor.execute("SELECT date FROM lates WHERE date = ?", (f"{day}/{month}/{year}",))
        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="That entry does not exist."
            )

        cursor.execute("DELETE FROM lates WHERE date = ?", (f"{day}/{month}/{year}",))
        app.state.db.commit()
    return {
        "date": f"{day}/{month}/{year}"
    }


if __name__ == "__main__":
    uvicorn.run(
        app=app,
        host="127.0.0.1",
        port=6969
    )  # runs the webserver on localhost:6969

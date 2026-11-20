import os
from pathlib import Path

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from psycopg.rows import dict_row

app = FastAPI()
WRITE_DB_HOST = os.environ["WRITE_DB_HOST"]
READ_DB_HOST = os.environ["READ_DB_HOST"]
DB_SETTINGS = {
    "dbname": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
    "connect_timeout": 3,
}


@app.get("/")
def index():
    return FileResponse(Path(__file__).with_name("index.html"))


@app.get("/api/orders")
def list_orders():
    try:
        with psycopg.connect(
            host=READ_DB_HOST, row_factory=dict_row, **DB_SETTINGS
        ) as conn:
            node = conn.execute(
                "SELECT pg_is_in_recovery() AS is_standby"
            ).fetchone()
            orders = conn.execute(
                "SELECT id, created_at FROM orders ORDER BY id DESC LIMIT 10"
            ).fetchall()
    except psycopg.Error as exc:
        raise HTTPException(503, f"Ошибка чтения с {READ_DB_HOST}") from exc

    return {"read_host": READ_DB_HOST, "is_standby": node["is_standby"], "orders": orders}


def insert_orders(count):
    try:
        with psycopg.connect(host=WRITE_DB_HOST, **DB_SETTINGS) as conn:
            last_id = conn.execute(
                """
                WITH inserted AS (
                    INSERT INTO orders (created_at)
                    SELECT now() FROM generate_series(1, %s::integer)
                    RETURNING id
                )
                SELECT max(id) FROM inserted
                """,
                (count,),
            ).fetchone()[0]
    except psycopg.Error as exc:
        raise HTTPException(503, f"Ошибка записи на {WRITE_DB_HOST}") from exc

    return {"write_host": WRITE_DB_HOST, "count": count, "last_id": last_id}


@app.post("/api/orders", status_code=201)
def create_order():
    return insert_orders(1)


@app.post("/api/orders/load", status_code=201)
def create_load():
    return insert_orders(1000)

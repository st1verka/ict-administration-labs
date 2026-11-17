from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI(title="ЛР № 1 — мониторинг")
index_page = Path(__file__).with_name("index.html")


@app.get("/", response_class=FileResponse)
async def home():
    return FileResponse(index_page, media_type="text/html")


@app.get("/health")
async def health():
    return {"status": "ok"}

import asyncio
from pathlib import Path
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="ЛР № 1 — мониторинг")
index_page = Path(__file__).with_name("index.html")


@app.get("/", response_class=FileResponse)
async def home():
    return FileResponse(index_page, media_type="text/html")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/error")
async def create_error():
    raise HTTPException(status_code=500, detail="Учебная ошибка")


@app.post("/delay")
async def create_delay():
    await asyncio.sleep(2)
    return {"delay_seconds": 2}


@app.post("/load")
async def create_load():
    request_count = 30

    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8000",
        timeout=3.0,
        trust_env=False,
    ) as client:
        responses = await asyncio.gather(
            *(client.get("/health") for _ in range(request_count)),
            return_exceptions=True,
        )

    succeeded = sum(
        isinstance(response, httpx.Response) and response.is_success
        for response in responses
    )
    result = {"sent": request_count, "succeeded": succeeded}

    if succeeded != request_count:
        raise HTTPException(status_code=503, detail=result)

    return result

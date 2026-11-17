import json
from datetime import UTC, datetime
import asyncio
from pathlib import Path
from time import perf_counter
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = FastAPI(title="ЛР № 1 — мониторинг")
index_page = Path(__file__).with_name("index.html")

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "route", "status"],
)
HTTP_ERRORS = Counter(
    "http_errors_total",
    "Total HTTP 5xx responses",
    ["method", "route"],
)
HTTP_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request handling time in seconds",
    ["method", "route"],
)


@app.middleware("http")
async def record_request(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    started_at = perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        route = getattr(request.scope.get("route"), "path", "unmatched")
        method = request.method
        elapsed = perf_counter() - started_at

        HTTP_REQUESTS.labels(method, route, str(status_code)).inc()
        HTTP_DURATION.labels(method, route).observe(elapsed)

        if 500 <= status_code < 600:
            HTTP_ERRORS.labels(method, route).inc()
        print(
            json.dumps(
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "level": "ERROR" if status_code >= 500 else "INFO",
                    "message": "HTTP request processed",
                    "method": method,
                    "route": route,
                    "status": status_code,
                    "duration_ms": round(elapsed * 1000, 2),
                    "trace_id": None,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(
        content=generate_latest(),
        headers={"Content-Type": CONTENT_TYPE_LATEST},
    )


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

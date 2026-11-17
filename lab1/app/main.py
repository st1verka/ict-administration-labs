from fastapi import FastAPI

app = FastAPI(title="ЛР № 1 — мониторинг")


@app.get("/health")
async def health():
    return {"status": "ok"}

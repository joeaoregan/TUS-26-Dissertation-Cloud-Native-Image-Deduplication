from fastapi import FastAPI

app = FastAPI(title="Image Dedupe Job API", version="0.5.0")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"status": "ready"}

from fastapi import FastAPI
from app.api.v1 import auth

app = FastAPI(title="Student Society & Welfare Portal")

app.include_router(auth.router)


@app.get("/")
def root():
    return {"status": "ok", "message": "Society Portal API is running"}
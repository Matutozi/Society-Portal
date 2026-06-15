from fastapi import FastAPI
from app.api.v1 import auth, societies, welfare

app = FastAPI(title="Student Society & Welfare Portal")

app.include_router(auth.router)
app.include_router(societies.router)
app.include_router(welfare.router)


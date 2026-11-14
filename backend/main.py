from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models
from database import Base, engine
from routers import profile, diet, advice, foods, auth

Base.metadata.create_all(engine)

app = FastAPI(title="膳食营养分析系统")
app.add_middleware(CORSMiddleware,
                   allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(diet.router, prefix="/api")
app.include_router(advice.router, prefix="/api")
app.include_router(foods.router, prefix="/api")


@app.get("/health")
def health():
    return {"ok": True}
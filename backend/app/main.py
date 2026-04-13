from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.mixes import router as mix_router
import app.models  # noqa: F401
from app.core.config import settings
from app.db.database import Base, engine, SessionLocal
from app.services.seed import seed_mixes


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_mixes(db, count=60)
    finally:
        db.close()


app.include_router(mix_router, prefix=settings.api_prefix)
app.mount("/generated", StaticFiles(directory="generated"), name="generated")
app.mount("/sample_data", StaticFiles(directory="sample_data"), name="sample_data")


@app.get("/")
def root():
    return {"message": "Concrete Mix Design Manager API", "docs": "/docs"}

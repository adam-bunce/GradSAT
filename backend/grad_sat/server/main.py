import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from grad_sat.server.routers import misc, graduation, time_tables

load_dotenv()

app = FastAPI()

app.include_router(misc.router)
app.include_router(graduation.router)
app.include_router(time_tables.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("UI_URL")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

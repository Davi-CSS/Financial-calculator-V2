from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
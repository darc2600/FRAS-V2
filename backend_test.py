from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hello():
    return "hello"

@app.get("/api/rooms")
def get_rooms():
    return []
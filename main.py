import fastapi

api = fastapi.FastAPI()


@api.get("/")
def index():
    return {"message": "Hello World!"}
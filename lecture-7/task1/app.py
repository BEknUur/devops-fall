from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"message": "hello"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/items/{item_id}")
def item(item_id: int):
    return {"id": item_id}

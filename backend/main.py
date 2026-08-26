from fastapi import FastAPI

app = FastAPI(title="GreenUpPCB LIS")

@app.get("/")
def root():
    return {"message": "GreenUpPCB LIS backend is running"}

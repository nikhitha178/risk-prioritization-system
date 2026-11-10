
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import router

app = FastAPI(
    title="Transaction Risk Prioritization System",
    description=(
        "A rule-based transaction monitoring and "
        "risk prioritization platform."
    ),
    version="1.0.0",
)

# Allow the React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def home():
    return {
        "message": "Transaction Risk Prioritization System is running!",
        "status": "success",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}

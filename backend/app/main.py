from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import market

app = FastAPI(
    title="Signaliers API",
    description="Backend API untuk analisis sinyal saham dan kripto real-time.",
    version="0.1.0"
)

# Konfigurasi CORS agar Frontend bisa mengakses API
origins = [
    "http://localhost:3000",
    "http://localhost:5173", # Default Vite port
    "http://localhost:5174", # Fallback Vite port
    "http://localhost:5175", # Current port
    "http://localhost:5176",
    "http://localhost:5177",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:5176",
    "http://127.0.0.1:5177",
    "https://signaliers.vercel.app", # Vercel Deployment
    "*", # Allow all for development/testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Daftarkan Router
app.include_router(market.router, prefix="/api", tags=["Market Analysis"])

@app.get("/")
async def root():
    return {"message": "Signaliers API is running!"}
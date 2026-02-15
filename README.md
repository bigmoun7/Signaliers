# Signaliers - Auto-Trading & Analysis Platform

A powerful technical analysis and paper trading platform featuring real-time charting, strategy backtesting, and live auto-trade simulation.

## Features

- **Real-Time Charting**: Interactive charts powered by Lightweight Charts.
- **Strategy Analysis**: Built-in strategies like PopGun Pattern and Bullish FVG.
- **Backtesting**: Validate strategies against historical data with IDR/USD conversion.
- **Paper Trading**: Simulate live trading with real-time market data and PnL tracking.
- **Market Scanning**: Scan multiple symbols for buy/sell signals.

## Project Structure

- `frontend/`: React + Vite application
- `backend/`: FastAPI Python application

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## How to Deploy

### Option 1: Full Deployment (Recommended)

1.  **Frontend (Vercel)**:
    *   Push this repo to GitHub.
    *   Import the repo in Vercel.
    *   Set Root Directory to `frontend`.
    *   Deploy.

2.  **Backend (Render/Railway)**:
    *   Push this repo to GitHub.
    *   Import in Render/Railway.
    *   Set Root Directory to `backend`.
    *   Build Command: `pip install -r requirements.txt`
    *   Start Command: `python -m uvicorn app.main:app --host 0.0.0.0 --port 10000` (or `$PORT`)

### Option 2: Quick Access (Tunneling)

If you want to access your *local* running app from the internet (e.g., on your phone) without deploying:

1.  **Use ngrok**:
    *   Download ngrok.
    *   Run `ngrok http 5173` (for frontend) - Note: Backend calls might fail if hardcoded to localhost.
    *   Better approach: Deploy backend first, then frontend.

## Git Instructions

1.  Create a new repository on GitHub.
2.  Run the following commands:

```bash
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git branch -M main
git push -u origin main
```

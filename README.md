# Rubik Blind 5-Style Backend API

High-performance REST API built with **FastAPI** and **MongoDB Atlas** designed to query and manage all **194,760+ 5-Style Blindfold Commutators** (126,720 edges + 68,040 corners) for the Rubik's Blind Helper app.

---

## Features

- **Blazing Fast**: FastAPI asynchronous core with sub-millisecond query responses.
- **MongoDB Atlas Integration**: Indexed collections (`edge5`, `corner5`) for fast sequence lookups ($O(1)$) and prefix searches.
- **Dynamic CORS**: Configurable CORS origins for secure production deployments with Angular, React, or mobile clients.
- **Interactive Documentation**: Auto-generated Swagger (`/docs`) and ReDoc (`/redoc`) specs.
- **Deployment-Ready**: Includes `Dockerfile`, `Procfile`, and `.env.example` for zero-friction deployments on Render, Railway, Fly.io, AWS, or Docker.

---

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **Server**: [Uvicorn](https://www.uvicorn.org/)
- **Database**: [MongoDB Atlas](https://www.mongodb.com/atlas) / PyMongo
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/)

---

## Local Development Setup

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/blindbackend.git
cd blindbackend
```

### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your MongoDB credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```env
MONGO_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=algorithem
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
```

### 5. Seed the Database (Optional)
If your MongoDB Atlas database is not yet populated:
```bash
python seed_db.py
```

### 6. Run the Application
```bash
# Using uvicorn directly with hot reload
uvicorn main:app --reload --port 8000

# Or run via Python
python main.py
```

- API Base URL: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health Check: `http://localhost:8000/health`

---

## Environment Variables Reference

| Variable | Default | Description |
| :--- | :--- | :--- |
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string (Atlas or local) |
| `DB_NAME` | `algorithem` | Database name containing `edge5` and `corner5` |
| `HOST` | `0.0.0.0` | Bind host address |
| `PORT` | `8000` | Port for the HTTP server (dynamically overridden by cloud providers) |
| `CORS_ORIGINS` | `*` | Comma-separated list of allowed origins (e.g. `https://my-app.vercel.app`) |

---

## Deployment Guide

### Option 1: Render / Railway / Heroku
1. Push your repository to GitHub.
2. Link your GitHub repo to **Render** or **Railway**.
3. Set the build and start commands:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}` (or use the provided `Procfile`)
4. Add environment variables in your deployment dashboard:
   - `MONGO_URI`: Your MongoDB Atlas connection string
   - `DB_NAME`: `algorithem`
   - `CORS_ORIGINS`: Your production frontend URL (e.g. `https://my-frontend.vercel.app`)

### Option 2: Docker
Build and run the container locally or on any container platform (Google Cloud Run, AWS ECS, Fly.io):

```bash
# Build Docker image
docker build -t blindbackend .

# Run container
docker run -p 8000:8000 --env-file .env blindbackend
```

---

## Key API Endpoints

- `GET /health` - Database connection status and record counts.
- `GET /api/5style/{piece_type}/letters` - Starting letters list (`edges` or `corners`).
- `GET /api/5style/{piece_type}/pairs?letter={A}&moves={4,5}` - Available letter pairs breakdown.
- `GET /api/5style/{piece_type}/by-pair?pair={AB}&page=1` - Paginated algorithms for letter pair.
- `GET /api/5style/{piece_type}/{sequence}` - Retrieve algorithm for sequence (e.g. `BEWQ`).
- `GET /api/5style/search?piece_type=corners&query=AB` - Search commutators by query prefix or letters.
- `PUT /api/5style/{piece_type}/{sequence}` - Update or customize commutator details.

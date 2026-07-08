# ─────────────────────────────────────────────────────────────────────────────
# SafeNet AI — Multi-Stage Dockerfile
#
# Stage 1 (builder): Compile the React/Vite frontend
# Stage 2 (runtime): Python 3.11 slim with FastAPI backend + built frontend
#
# Build:
#   docker build -t safenet-ai .
#
# Run:
#   docker run -p 8000:8000 \
#     -e FIREWORKS_API_KEY=your_key \
#     -e GEMINI_API_KEY=your_key \
#     safenet-ai
#
# AMD Developer Cloud:
#   Push this image to any registry and deploy on AMD Developer Cloud.
#   The Python inference stack automatically uses AMD hardware via ROCm
#   if the host exposes /dev/kfd and /dev/dri (no code changes needed).
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Frontend builder ─────────────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Install dependencies first (cached layer)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --prefer-offline

# Copy source and build
COPY frontend/ ./
RUN npm run build
# Output: /app/frontend/dist


# ── Stage 2: Python runtime ───────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# System packages needed for OpenCV, NumPy, PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────────
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ── Backend source ────────────────────────────────────────────────────────────
COPY backend/ ./backend/
COPY data/ ./data/
COPY api/ ./api/

# ── Built frontend (served as static files by FastAPI) ───────────────────────
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# ── Static file serving: mount frontend/dist under FastAPI ────────────────────
# This is done in main.py via StaticFiles mount — see the ENV var below.
ENV FRONTEND_DIST_PATH=/app/frontend/dist

# ── Runtime config ─────────────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_ENV=production

# API keys — supply at runtime via -e or docker-compose env_file
ENV FIREWORKS_API_KEY=""
ENV GEMINI_API_KEY=""
ENV OPENAI_API_KEY=""

EXPOSE 8000

# ── Health check ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# ── Entrypoint ────────────────────────────────────────────────────────────────
WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

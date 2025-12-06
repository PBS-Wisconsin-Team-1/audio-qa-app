# Multi-stage build for Audio QA Application

# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend with built frontend
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY audio_files/ ./audio_files/
COPY detection_results/ ./detection_results/
COPY pyproject.toml .
COPY LICENSE .
COPY README.md .

# Copy built frontend from stage 1
COPY --from=frontend-builder /frontend/build ./frontend/build

# Install the package (using pyproject.toml)
RUN pip install -e .

# Create necessary directories
RUN mkdir -p audio_files detection_results

# Expose ports
# 5001 - Flask API server
# 3000 - Frontend (if running dev server)
# 9181 - RQ Dashboard
EXPOSE 5001 3000 9181

# Set environment variables
ENV PYTHONUNBUFFERED=1

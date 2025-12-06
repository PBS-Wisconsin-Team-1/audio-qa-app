# Docker Deployment Guide - Audio QA Application

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed (includes Docker Compose)
- At least 4GB RAM available for Docker

### Basic Usage

1. **Start the application:**
   ```bash
   docker-compose up
   ```
   This starts Redis, Worker, and API server.

2. **Access the application:**
   - API Server: http://localhost:5001
   - Upload files to: `./audio_files/`
   - Results appear in: `./detection_results/`

3. **Stop the application:**
   ```bash
   docker-compose down
   ```

---

## Advanced Usage

### With RQ Dashboard (for monitoring jobs)
```bash
docker-compose --profile with-dashboard up
```
- Dashboard: http://localhost:9181

### With Frontend Development Server
```bash
docker-compose --profile development up
```
- Frontend: http://localhost:3000
- API: http://localhost:5001

### Both Dashboard and Frontend
```bash
docker-compose --profile with-dashboard --profile development up
```

### Run in Background (Detached Mode)
```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f
```

---

## Service Architecture

| Service | Port | Description |
|---------|------|-------------|
| `redis` | 6379 | Job queue backend |
| `worker` | - | Processes audio detection jobs |
| `api` | 5001 | Flask REST API |
| `dashboard` | 9181 | RQ Dashboard (optional) |
| `frontend` | 3000 | React dev server (optional) |

---

## Volume Mounts

The following directories are mounted from your host:
- `./audio_files` → `/app/audio_files` (input audio files)
- `./detection_results` → `/app/detection_results` (output JSON results)

Files placed in these directories are accessible to the containers.

---

## Useful Commands

### Rebuild after code changes
```bash
docker-compose build
docker-compose up
```

### View running containers
```bash
docker-compose ps
```

### Execute commands in a container
```bash
# Run CLI in worker container
docker-compose exec worker auqa-cli

# Access Redis CLI
docker-compose exec redis redis-cli
```

### Scale workers (run multiple)
```bash
docker-compose up --scale worker=1
```

### Clean up everything
```bash
docker-compose down -v  # Removes volumes too
```

---

## Production Deployment

### Build optimized images
```bash
docker-compose build --no-cache
```

### Run with restart policies
Already configured with `restart: unless-stopped` for production use.

### Environment Variables

Create a `.env` file:
```env
REDIS_URL=redis://redis:6379
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

Then:
```bash
docker-compose --env-file .env up
```

---

## Troubleshooting

### Port already in use
Change ports in `docker-compose.yml`:
```yaml
ports:
  - "5002:5001"  # Use 5002 instead of 5001
```

### Container fails to start
Check logs:
```bash
docker-compose logs api
docker-compose logs worker
```

### Redis connection issues
Ensure Redis is healthy:
```bash
docker-compose exec redis redis-cli ping
# Should return: PONG
```

### Rebuild from scratch
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

---

## Distribution to End Users

### Option 1: Docker Hub
```bash
# Build and tag
docker build -t yourusername/audio-qa-app:latest .

# Push to Docker Hub
docker push yourusername/audio-qa-app:latest
```

Users can then run:
```bash
docker pull yourusername/audio-qa-app:latest
docker-compose up
```

### Option 2: Save as TAR file
```bash
# Save images
docker save -o audio-qa-app.tar audio-qa-app

# Users load the image
docker load -i audio-qa-app.tar
docker-compose up
```

### Option 3: Share the repository
Users clone the repo and run:
```bash
git clone <your-repo-url>
cd audio-qa-app
docker-compose up
```

---

## Development Workflow

1. **Make code changes** in `src/` or `frontend/`
2. **Rebuild** specific service:
   ```bash
   docker-compose build api
   docker-compose up api
   ```
3. **Or use bind mounts** for live reload (advanced):
   ```yaml
   volumes:
     - ./src:/app/src:ro
   ```

---

## Health Checks

Services include health checks:
```bash
# Check API health
curl http://localhost:5001/api/health

# Check Redis health
docker-compose exec redis redis-cli ping
```

---

## Resource Limits

Add to `docker-compose.yml` if needed:
```yaml
services:
  worker:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

---

## Support

For issues, check:
1. `docker-compose logs`
2. Ensure Docker Desktop is running
3. Verify ports aren't in use: `netstat -an | findstr "5001 6379 9181"`

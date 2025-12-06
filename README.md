# Audio QA App (Quick Start)

![AuQA Screenshot](assets/AuQA_screenshot.png)

## Install Dependencies

1. Clone the repository and enter the directory:
	```bash
	git clone https://github.com/PBS-Wisconsin-Team-1/audio-qa-app.git
	cd audio-qa-app
	```
2. Create and activate a virtual environment:
	```bash
	python -m venv .venv
	# On Windows (PowerShell)
	.venv\Scripts\Activate.ps1
	# On macOS/Linux
	source .venv/bin/activate
	```
3. Install dependencies:
	```bash
	pip install -r requirements.txt
	```

## Redis Server Required

You must have a Redis server running and its executable in your PATH. On Windows, download from https://github.com/tporadowski/redis/releases. On macOS/Linux, install via your package manager. The default connection is `localhost:6379`.

## Running the App

To start all services (Redis, RQ dashboard, workers, job queue CLI) at once, use:

**Windows (PowerShell):**
```powershell
cd scripts
./start_all.ps1
```

**macOS/Linux:**
```bash
cd scripts
bash start_all.sh
```
After starting, view the RQ dashboard at: [http://localhost:9181](http://localhost:9181)


To stop all services:

**Windows:**
```powershell
./stop_all.ps1
```
**macOS/Linux:**
```bash
bash stop_all.sh
```

**Start AuQA Dashboard UI**
```bash
cd frontend
npm install
npm start
```

## Docker Setup

This project supports full containerization using Docker and Docker Compose. All services (API, worker, CLI, dashboard, frontend, Redis) are defined in `docker-compose.yml` for easy, consistent deployment across devices.

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/PBS-Wisconsin-Team-1/audio-qa-app.git
   cd audio-qa-app
   ```
2. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```
   This will build the backend image and start all containers. The first build may take several minutes.

   You can optionally set an `AUDIO_FILES_PATH` environment variable before running docker compose to change the audio folder to select audio files from.

   ```bash
	$env:AUDIO_FILES_PATH = "C:\path\to\your\audio_files"
   ```
   *Note: When running with docker, cannot change the audio file path. You must restart the app and change to the new directory using the environment variable.*   

3. **Access the app:**
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - API: [http://localhost:5001/api](http://localhost:5001/api)
   - RQ Dashboard: [http://localhost:9181](http://localhost:9181) (optional)

4. **Stop all services:**
   ```bash
   docker-compose down
   ```
Refer to DOCKER.md for more building options

---
For more details, see the [GitHub repository](https://github.com/PBS-Wisconsin-Team-1/audio-qa-app).
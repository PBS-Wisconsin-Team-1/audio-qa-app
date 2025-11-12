
# Audio QA App (Quick Start)

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

## Dashboard & Monitoring



You can also run the interactive console app:
```bash
cd src/console_app
python main.py
```

## Frontend (React Web App)

The React frontend provides a web interface for viewing detection results and managing audio files.

### Setup

1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

2. Start the Flask API server (in a separate terminal):
```bash
# Option 1: From project root
python src/api_server.py

# Option 2: Use helper script (from project root)
./scripts/start_api.sh
# On Windows:
# .\scripts\start_api.ps1
```

3. Start the React development server:
```bash
cd frontend
npm start
```

The frontend will be available at [http://localhost:3000](http://localhost:3000)

**Note:** The API server runs on port 5001 by default (instead of 5000) to avoid conflicts with macOS AirPlay Receiver. If you need to use a different port, set the `API_PORT` environment variable or update the frontend's `.env` file.

### Features

- **Gallery View**: Browse all processed audio files with issue counts
- **Queue Progress**: Real-time monitoring of job queue status
- **File Upload**: Upload audio files for processing (optional)
- **Issue Detection**: View detailed detection results including:
  - Issue type (Clipping, Cutout, etc.)
  - Timing information (start/end times)
  - Detection parameters
  - Detailed descriptions
- **Export Reports**: Download text file summaries of all detected issues

---
For more details, see the [GitHub repository](https://github.com/PBS-Wisconsin-Team-1/audio-qa-app).
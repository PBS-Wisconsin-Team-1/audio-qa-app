# Audio QA App

An automated audio question-answering application that processes audio files and provides intelligent responses to questions about the audio content.

## Overview

This application leverages machine learning and natural language processing to analyze audio content and answer questions about it. The system can process various audio formats and provide accurate, contextual answers based on the audio's content.

## Prerequisites

Python 3.10 or higher

## Installation (Can use uv but not explicitly shown below)

1. Clone the repository:
	```bash
	git clone https://github.com/PBS-Wisconsin-Team-1/audio-qa-app.git
	cd audio-qa-app
	```

2. Create and activate a virtual environment:
	```bash
	python -m venv .venv
	# On Windows (PowerShell)
	.venv\Scripts\Activate.ps1
	# On Windows (Command Prompt)
	.venv\Scripts\activate.bat
	# On macOS/Linux
	source .venv/bin/activate
	```

3. Install dependencies:
	```bash
	pip install -r requirements.txt
	```

## Usage

### Run the Interactive Console App

Navigate to the `src/console_app` folder:
```bash
cd src/console_app
```
Run the interactive console app:
```bash
python main.py
```

### Run the Job Queue CLI

Navigate to the `src/job_queue` folder:
```bash
cd src/job_queue
```
Run the job queue CLI:
```bash
python queue.py
```

Follow the prompts to queue jobs for audio detection or artifact simulation.

**Note:** Ensure Redis is running locally (default settings) before using job queue features.

To start an RQ worker (in a separate terminal, from the project root):
```bash
rq worker
```

This will process jobs you queue from the CLI.

### Redis Server Setup (Required for Job Queue and Dashboard)

You must have a Redis server running for the job queue and dashboard features to work.

#### Windows
1. Download Redis for Windows from: https://github.com/tporadowski/redis/releases
2. Extract the zip to a folder (e.g., `C:\Redis`).
3. Start the server:
   ```powershell
   cd C:\Redis
   .\redis-server.exe
   ```

#### macOS (Homebrew)
```bash
brew install redis
brew services start redis
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

The default connection is `localhost:6379`. If you use a different host/port, set the connection in your Python code or with environment variables.

You can now use the job queue CLI and run `rq-dashboard` to monitor jobs.


### One-Command Startup & Cleanup Scripts

You can use the provided scripts in the `scripts` folder to start and stop all related services (Redis, RQ dashboard, workers, and the job queue CLI) together. These scripts manage process IDs and ensure a clean startup and shutdown.

#### Windows (PowerShell)
From the project root, run:
```powershell
./scripts/start_all.ps1
```
This will open new PowerShell windows for the Redis server, RQ dashboard, RQ workers, and the job queue CLI. All process IDs are tracked in `scripts/tmp/auqa-pids.txt`.

To stop all started processes, run:
```powershell
./scripts/stop_all.ps1
```
This will recursively terminate all processes started by `start_all.ps1` (including any child processes) and clean up the PID file.

#### macOS/Linux (Bash)
From the project root, run:
```bash
bash scripts/start_all.sh
```
This will start all services (Redis, dashboard, workers, CLI) in new terminal windows and record their PIDs in `scripts/tmp/auqa-pids.txt`.

To stop all started processes, run:
```bash
bash scripts/stop_all.sh
```
This will recursively terminate all processes started by `start_all.sh` and clean up the PID file.

Make sure you have the necessary permissions to execute these scripts (you may need to run `chmod +x scripts/start_all.sh scripts/stop_all.sh` on macOS/Linux).

**Note:** If you manually close a window or process, it may not be removed from the PID file. Running the stop script is the recommended way to clean up all related processes.

## Acknowledgments

- Built by PBS Wisconsin Team 1
- Thanks to the open-source community for the tools and libraries

## Roadmap

- [ ] Support for real-time audio processing
- [ ] Multi-language support
- [ ] Enhanced accuracy with larger models
- [ ] Integration with cloud storage services
- [ ] Mobile application support

---

For more detailed documentation, visit our [GitHub repository](https://github.com/PBS-Wisconsin-Team-1/audio-qa-app).
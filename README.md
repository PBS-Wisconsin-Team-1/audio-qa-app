
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

---
For more details, see the [GitHub repository](https://github.com/PBS-Wisconsin-Team-1/audio-qa-app).
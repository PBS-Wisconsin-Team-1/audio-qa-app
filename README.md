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
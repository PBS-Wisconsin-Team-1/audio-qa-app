# Audio QA App

An automated audio question-answering application that processes audio files and provides intelligent responses to questions about the audio content.

## Overview

This application leverages machine learning and natural language processing to analyze audio content and answer questions about it. The system can process various audio formats and provide accurate, contextual answers based on the audio's content.

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager

## Installation with uv (Optional)

### 1. Install uv (if not already installed)

#### Windows (PowerShell)
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### macOS/Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone the repository
```bash
git clone https://github.com/PBS-Wisconsin-Team-1/audio-qa-app.git
cd audio-qa-app
```

### 3. Create and activate virtual environment
```bash
# Create virtual environment
uv venv

# Activate virtual environment
# On Windows (PowerShell)
.venv\Scripts\Activate.ps1

# On Windows (Command Prompt)
.venv\Scripts\activate.bat

# On macOS/Linux
source .venv/bin/activate
```

### 4. Install dependencies
```bash
# Install production dependencies
uv pip install -r requirements.txt

# Or install the project in development mode with dev dependencies
uv pip install -e .[dev]
```

## Acknowledgments

- Built by PBS Wisconsin Team 1
- Powered by state-of-the-art machine learning models
- Thanks to the open-source community for the tools and libraries

## Roadmap

- [ ] Support for real-time audio processing
- [ ] Multi-language support
- [ ] Enhanced accuracy with larger models
- [ ] Integration with cloud storage services
- [ ] Mobile application support

---

For more detailed documentation, visit our [GitHub repository](https://github.com/PBS-Wisconsin-Team-1/audio-qa-app).
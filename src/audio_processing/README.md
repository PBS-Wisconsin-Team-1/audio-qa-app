# Audio Processing Module

This module contains tools for loading, analyzing, and simulating artifacts in audio files.

## Files Overview

- **`audio_import.py`** - Load and batch process audio files
- **`artifact_simulate.py`** - Insert artificial audio artifacts (clicks, pops, cutouts, clipping)
- **`distortion_detection.py`** - Detect and analyze audio distortion
- **`__init__.py`** - Package initialization

---

## Command-Line Usage

### 1. Audio Import (`audio_import.py`)

Load and display information about audio files.

**Usage:**
```bash
python src/audio_processing/audio_import.py
```

**Description:**
- Loads all audio files from the default directory (`./audio_files`)
- Displays filename, sample count, and sample rate for each file
- Supports formats: `.wav`, `.flac`, `.ogg`, `.mp3`, `.m4a`

**Example Output:**
```
Loading audio files from: ./audio_files
Loading: ./audio_files/ex1.wav
ex1.wav: (132300,), 22050 Hz
```

---

### 2. Artifact Simulation (`artifact_simulate.py`)

Insert artificial audio artifacts into audio files for testing detection algorithms.

**Usage:**
```bash
python src/audio_processing/artifact_simulate.py input.wav output.wav [-d directory]
```

**Arguments:**
- `input.wav` - Input audio filename (must be in the audio directory)
- `output.wav` - Output filename for the distorted audio
- `-d directory` - (Optional) Path to audio files directory (default: `./audio_files`)

**Examples:**
```bash
# Use default directory (./audio_files)
python src/audio_processing/artifact_simulate.py ex1.wav ex1_distorted.wav

# Specify custom directory
python src/audio_processing/artifact_simulate.py ex1.wav ex1_distorted.wav -d "./my_audio"

# From audio_processing directory
cd src/audio_processing
python artifact_simulate.py ex1.wav ex1_distorted.wav -d "../../audio_files"
```

**Output:**
```
=== Inserting artifacts into ex1.wav ===
Click #1 at 00:12.45
Click #2 at 00:43.21
Pop #1 at 01:05.67
Pop #2 at 01:32.89
Cutout #1 at 00:25.34
Cutout #2 at 01:15.78
Clipping #1 at 00:50.12
Clipping #2 at 01:40.23

✓ Distorted audio saved to ex1_distorted.wav
Total artifacts inserted: 8
```

**Default Artifacts:**
- 2 clicks (short white noise bursts, ~5ms)
- 2 pops (longer white noise bursts, ~20ms)
- 2 cutouts (silent gaps, ~100ms)
- 2 clipping events (hard clipping, ~50ms)

**Customization:**
To customize artifact counts, use the `ArtifactSim` class in Python:
```python
from audio_processing import artifact_simulate

# Custom artifact configuration
artifacts = {'clicks': 5, 'pops': 3, 'cutouts': 1, 'clipping': 4}
sim = artifact_simulate.ArtifactSim(artifacts=artifacts)
sim.distort_audio('ex1.wav', 'ex1_custom.wav')
```

---

### 3. Distortion Detection (`distortion_detection.py`)

*(Currently designed for programmatic use, not command-line)*

Analyze audio for distortion using THD (Total Harmonic Distortion) and clipping detection.

**Python Usage:**
```python
from audio_processing import distortion_detection
import numpy as np

# Load your audio data (numpy array)
audio_data = ...  # your audio as numpy array

# Calculate Total Harmonic Distortion
thd = distortion_detection.thd_ratio(audio_data)

# Detect clipping
has_clipping = distortion_detection.detect_clipping(audio_data)

print(f"THD: {thd}, Clipping: {has_clipping}")
```

---

## Module Usage (Python)

All modules can also be imported and used programmatically:

```python
from audio_processing import audio_import, artifact_simulate, distortion_detection

# Load audio files
loader = audio_import.AudioLoader(directory="./audio_files")
data = loader.load_batch(['ex1.wav', 'ex2.wav'])

# Simulate artifacts
sim = artifact_simulate.ArtifactSim()
artifacts = sim.distort_audio('ex1.wav', 'ex1_distorted.wav')

# Detect distortion
for name, info in data.items():
    thd = distortion_detection.thd_ratio(info['data'])
    clipping = distortion_detection.detect_clipping(info['data'])
    print(f"{name}: THD={thd}, Clipping={clipping}")
```

---

## Requirements

Install dependencies:
```bash
pip install librosa numpy pydub
```

Or using uv:
```bash
uv pip install librosa numpy pydub
```

---

## Directory Structure

```
audio-qa-app/
├── audio_files/          # Default audio file directory
│   ├── ex1.wav
│   ├── ex2.wav
│   └── ...
└── src/
    └── audio_processing/
        ├── __init__.py
        ├── audio_import.py
        ├── artifact_simulate.py
        ├── distortion_detection.py
        └── README.md
```

---

## Notes

- All timestamps in `artifact_simulate.py` are displayed in `mm:ss.ms` format
- Audio files must be in supported formats: WAV, FLAC, OGG, MP3, M4A
- Default sample rate is 22050 Hz (configurable in `AudioLoader`)
- All audio is converted to mono by default (configurable in `AudioLoader`)

import os
import json
import redis
from rq import Queue
from audio_processing.audio_import import AudioLoader
from .worker import AudioDetectionJob, simulate_artifacts
from .analysis_types import USER_JOB_TYPES, ANALYSIS_TYPES
import multiprocessing
from typing import List


# Get the project root directory (two levels up from this file)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DEFAULT_AUDIO_DIR = os.path.join(PROJECT_ROOT, "audio_files")

# Config file to store audio directory preference (shared with API server)
CONFIG_FILE = os.path.join(PROJECT_ROOT, '.audio_qa_config.json')

def get_audio_files_dir():
    """Get the configured audio files directory, or default if not set."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                audio_dir = config.get('audio_files_dir')
                if audio_dir and os.path.exists(audio_dir):
                    return audio_dir
        except Exception as e:
            print(f"Warning: Error reading config file: {e}")
    return DEFAULT_AUDIO_DIR

# Use the configured directory (or default)
AUDIO_DIR = get_audio_files_dir()


def parse_indices(raw: str, max_index: int) -> List[int]:
    """Parse a comma-separated list of indices (1-based). Returns unique 0-based indices."""
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(',') if p.strip()]
    indices = set()
    for p in parts:
        if p.lower() in ('all', '*'):
            return list(range(max_index))
        try:
            i = int(p) - 1
            if 0 <= i < max_index:
                indices.add(i)
        except ValueError:
            continue
    return sorted(indices)


def safe_input(prompt: str, default: str = "") -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return default


def clear_screen():
    """Clear the terminal screen (cross-platform)."""
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except Exception:
        pass


def main():
    multiprocessing.set_start_method("spawn", force=True)
    # Get the current configured directory (in case it changed)
    audio_dir = get_audio_files_dir()
    loader = AudioLoader(directory=audio_dir)

    # Establish Redis connection and validate
    try:
        redis_conn = redis.from_url("redis://localhost:6379/0")
        redis_conn.ping()
    except Exception as exc:
        print(f"Warning: could not connect to Redis at default URL: {exc}")
        print("Please ensure a Redis server is running and reachable before queueing jobs.")
        return

    job_queue = Queue(connection=redis_conn)

    while True:
        clear_screen()
        print(f"Using audio directory: {audio_dir}")
        print("Audio QA Job Queue CLI")
        print("\nMenu:")
        print("1. Queue audio detection jobs")
        print("2. Queue simulate_artifact job")
        print("3. Exit")
        choice = safe_input("Select an option: ")

        if get_audio_files_dir() != loader.directory:
            audio_dir = get_audio_files_dir()
            print(f"Audio directory changed. Using new directory: {audio_dir}")
            loader = AudioLoader(directory=audio_dir)

        if choice == "1":
            clear_screen()
            det_types = list(ANALYSIS_TYPES.keys())
            print("Available detection types:")
            for i, det_type in enumerate(det_types, 1):
                print(f"  {i}. {det_type}")

            raw = safe_input("Enter detection type numbers to run (comma-separated, e.g. '1,3' or 'all'): ")
            det_indices = parse_indices(raw, len(det_types))
            if not det_indices:
                print("No valid detection types selected. Skipping.")
                safe_input("Press Enter to continue...")
                continue

            detection_params = {}
            for idx in det_indices:
                det_type = det_types[idx]
                param_dict = {}
                param_specs = ANALYSIS_TYPES[det_type].get('params', {})
                for param, param_type in param_specs.items():
                    val = safe_input(f"Enter value for {det_type} parameter '{param}' ({param_type.__name__}) [press Enter to skip]: ")
                    if val == "":
                        continue
                    try:
                        param_dict[param] = param_type(val)
                    except Exception:
                        print(f"Invalid value for {param}; ignoring and using defaults later.")
                detection_params[det_type] = param_dict

            files = loader.get_file_list()
            if not files:
                print("No audio files found in audio directory.")
                safe_input("Press Enter to continue...")
                continue
            clear_screen()
            print(f"Available audio files ({loader.directory}):")
            for i, f in enumerate(files, 1):
                print(f"  {i}. {f}")
            raw_files = safe_input("Enter audio file numbers to process (comma-separated, e.g. '1,2' or 'all'): ")
            file_indices = parse_indices(raw_files, len(files))
            if not file_indices:
                print("No valid files selected. Skipping.")
                safe_input("Press Enter to continue...")
                continue

            selected_files = [files[i] for i in file_indices]
            for audio_file_path in selected_files:
                # Validate file exists
                abs_path = os.path.join(loader.directory, audio_file_path)
                if not os.path.exists(abs_path):
                    print(f"File not found: {abs_path}; skipping.")
                    safe_input("Press Enter to continue...")
                    continue
                job = AudioDetectionJob(loader, audio_file_path)
                try:
                    job_queue.enqueue(job.load_and_queue, detection_params)
                    print(f"Queued detection job for {audio_file_path}")
                except Exception as exc:
                    print(f"Failed to enqueue job for {audio_file_path}: {exc}")
                    safe_input("Press Enter to continue...")

        elif choice == "2":
            clear_screen()
            audio_file_path = safe_input("Enter audio file path for simulation: ")
            if not audio_file_path:
                print("No file provided; aborting.")
                safe_input("Press Enter to continue...")
                continue
            abs_path = os.path.join(audio_dir, audio_file_path)
            if not os.path.exists(abs_path):
                print(f"File not found: {abs_path}; aborting.")
                safe_input("Press Enter to continue...")
                continue
            try:
                job = job_queue.enqueue(simulate_artifacts, AudioLoader(directory=audio_dir), audio_file_path, {})
                print(f"Queued simulate_artifact job for {audio_file_path}")
            except Exception as exc:
                print(f"Failed to enqueue simulate_artifacts: {exc}")
                safe_input("Press Enter to continue...")

        elif choice == "3":
            print("Exiting.")
            break
        else:
            print("Invalid option. Please try again.")
        # Pause before refreshing menu
        safe_input("Press Enter to continue...")


if __name__ == "__main__":
    main()
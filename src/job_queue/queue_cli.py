import os
import redis
from rq import Queue
from audio_processing.audio_import import AudioLoader
import os
import redis
from rq import Queue
from audio_processing.audio_import import AudioLoader
from worker import AudioDetectionJob, simulate_artifacts
from analysis_types import USER_JOB_TYPES, ANALYSIS_TYPES
import multiprocessing
from typing import List


AUDIO_DIR = os.path.join("..", "..", "audio_files")


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


def main():
    multiprocessing.set_start_method("spawn", force=True)
    loader = AudioLoader(directory=AUDIO_DIR)

    # Establish Redis connection and validate
    try:
        redis_conn = redis.from_url("redis://localhost:6379/0")
        redis_conn.ping()
    except Exception as exc:
        print(f"Warning: could not connect to Redis at default URL: {exc}")
        print("Please ensure a Redis server is running and reachable before queueing jobs.")
        return

    job_queue = Queue(connection=redis_conn)

    print("Audio QA Job Queue CLI")
    while True:
        print("\nMenu:")
        print("1. Queue audio detection jobs")
        print("2. Queue simulate_artifact job")
        print("3. Exit")
        choice = safe_input("Select an option: ")

        if choice == "1":
            det_types = list(ANALYSIS_TYPES.keys())
            print("Available detection types:")
            for i, det_type in enumerate(det_types, 1):
                print(f"  {i}. {det_type}")

            raw = safe_input("Enter detection type numbers to run (comma-separated, e.g. '1,3' or 'all'): ")
            det_indices = parse_indices(raw, len(det_types))
            if not det_indices:
                print("No valid detection types selected. Skipping.")
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
                continue
            print("Available audio files:")
            for i, f in enumerate(files, 1):
                print(f"  {i}. {f}")
            raw_files = safe_input("Enter audio file numbers to process (comma-separated, e.g. '1,2' or 'all'): ")
            file_indices = parse_indices(raw_files, len(files))
            if not file_indices:
                print("No valid files selected. Skipping.")
                continue

            selected_files = [files[i] for i in file_indices]
            for audio_file_path in selected_files:
                # Validate file exists
                abs_path = os.path.join(loader.directory, audio_file_path)
                if not os.path.exists(abs_path):
                    print(f"File not found: {abs_path}; skipping.")
                    continue
                job = AudioDetectionJob(loader, audio_file_path)
                try:
                    job_queue.enqueue(job.load_and_queue, detection_params)
                    print(f"Queued detection job for {audio_file_path}")
                except Exception as exc:
                    print(f"Failed to enqueue job for {audio_file_path}: {exc}")

        elif choice == "2":
            audio_file_path = safe_input("Enter audio file path for simulation: ")
            if not audio_file_path:
                print("No file provided; aborting.")
                continue
            abs_path = os.path.join(AUDIO_DIR, audio_file_path)
            if not os.path.exists(abs_path):
                print(f"File not found: {abs_path}; aborting.")
                continue
            try:
                job = job_queue.enqueue(simulate_artifacts, AudioLoader(directory=AUDIO_DIR), audio_file_path, {})
                print(f"Queued simulate_artifact job for {audio_file_path}")
            except Exception as exc:
                print(f"Failed to enqueue simulate_artifacts: {exc}")

        elif choice == "3":
            print("Exiting.")
            break
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()
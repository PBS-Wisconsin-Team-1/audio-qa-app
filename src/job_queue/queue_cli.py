import os
import redis
from rq import Queue
from audio_processing.audio_import import AudioLoader
from worker import AudioDetectionJob, simulate_artifacts
from analysis_types import USER_JOB_TYPES, ANALYSIS_TYPES
import multiprocessing

AUDIO_DIR = os.path.join("..", "..", "audio_files")

def main():
    multiprocessing.set_start_method("spawn", force=True)
    loader = AudioLoader(directory=AUDIO_DIR)
    redis_conn = redis.Redis()
    job_queue = Queue(connection=redis_conn)

    print("Audio QA Job Queue CLI")
    while True:
        print("\nMenu:")
        print("1. Queue audio detection jobs")
        print("2. Queue simulate_artifact job")
        print("3. Exit")
        choice = input("Select an option: ").strip()

        if choice == "1":
            print("Available detection types:")
            for i, det_type in enumerate(ANALYSIS_TYPES.keys(), 1):
                print(f"  {i}. {det_type}")
            det_indices = input("Enter detection type numbers to run (comma-separated): ").strip().split(",")
            detection_params = {}
            for idx in det_indices:
                try:
                    idx = int(idx.strip()) - 1
                    det_type = list(ANALYSIS_TYPES.keys())[idx]
                except (ValueError, IndexError):
                    print(f"Invalid detection type index: {idx+1}")
                    continue
                param_dict = {}
                for param, param_type in ANALYSIS_TYPES[det_type]['params'].items():
                    val = input(f"Enter value for {det_type} parameter '{param}' ({param_type.__name__}): ")
                    try:
                        param_dict[param] = param_type(val)
                    except Exception:
                        print(f"Invalid value for {param}, using default if available.")
                detection_params[det_type] = param_dict

            print("Available audio files:")
            files = loader.get_file_list()
            for i, f in enumerate(files, 1):
                print(f"  {i}. {f}")
            file_indices = input("Enter audio file numbers to process (comma-separated): ").strip().split(",")
            selected_files = []
            for idx in file_indices:
                try:
                    idx = int(idx.strip()) - 1
                    selected_files.append(files[idx])
                except (ValueError, IndexError):
                    print(f"Invalid file index: {idx+1}")
            for audio_file_path in selected_files:
                job = AudioDetectionJob(loader, audio_file_path)
                job_queue.enqueue(job.load_and_queue, detection_params)
                print(f"Queued detection job for {audio_file_path}")

        elif choice == "2":
            audio_file_path = input("Enter audio file path for simulation: ").strip()
            job = job_queue.enqueue(simulate_artifacts, audio_file_path)
            print(f"Queued simulate_artifact job for {audio_file_path}")

        elif choice == "3":
            print("Exiting.")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
import redis
from rq import Queue
from audio_processing.audio_import import AudioLoader
from worker import AudioDetectionJob, simulate_artifacts


def main():
    loader = AudioLoader()
    job_queue = Queue(connection=redis.Redis())

    print("Audio QA Job Queue CLI")
    while True:
        print("\nMenu:")
        print("1. Queue audio detection jobs")
        print("2. Queue simulate_artifact job")
        print("3. Exit")
        choice = input("Select an option: ").strip()

        if choice == "1":
            print("Enter detection types to run (comma-separated, e.g. distortion, clipping):")
            detection_types = input().strip().split(",")
            detection_params = {}
            for det in detection_types:
                det = det.strip()
                params = input(f"Enter parameters for '{det}' as key=value pairs (comma-separated): ").strip()
                param_dict = {}
                if params:
                    for pair in params.split(","):
                        if "=" in pair:
                            k, v = pair.split("=", 1)
                            param_dict[k.strip()] = v.strip()
                detection_params[det] = param_dict
            audio_files_input = input("Enter audio file paths (comma-separated): ").strip()
            files = [f.strip() for f in audio_files_input.split(",") if f.strip()]
            for audio_file_path in files:
                job = AudioDetectionJob(job_queue, loader)
                job.load_and_queue(audio_file_path, detection_types, detection_params)
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
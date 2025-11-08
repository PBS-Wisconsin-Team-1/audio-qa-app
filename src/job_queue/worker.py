import os
import json
import redis
from audio_processing.audio_import import AudioLoader
from audio_processing.utils import Detection, seconds_to_mmss, fill_default_params
from typing import Type
from rq import Queue
from audio_processing.artifact_simulate import ArtifactSim
from analysis_types import ANALYSIS_TYPES
from datetime import datetime

OUTPUT_DIR = os.path.join("..", "..", "detection_results")

class AudioDetectionJob:
    def __init__(self, loader: Type[AudioLoader], audio_file_path: str, redis_url: Type[str] = 'redis://localhost:6379/0'):
        self.redis_url = redis_url
        self.loader = loader
        self.completed = {}
        self.audio_file = audio_file_path
        self.audio = None
        self.job_ids = []
        self.audio_base = os.path.splitext(os.path.basename(self.audio_file))[0]
        self.start_timestamp = int(datetime.now().timestamp())

    def load_and_queue(self, analyses: dict):
        redis_conn = redis.from_url(self.redis_url)
        job_queue = Queue(connection=redis_conn)
        self.audio = self.loader.load_audio_file(self.audio_file)

        for analysis_type in analyses.keys():
            self.job_ids.append(f"{self.audio_base}_{analysis_type}_{self.start_timestamp}")
            redis_conn.hset("job_status", f"{self.audio_base}_{analysis_type}_{self.start_timestamp}", "queued")

        for analysis_type, analysis_params in analyses.items():
            job_queue.enqueue(self.run_detection, analysis_type, analysis_params)
        return
        
    def run_detection(self, type: str, params: dict):
        redis_conn = redis.from_url(self.redis_url)
        print(f"Running detection {type} on {self.audio_file}")
        det_result = ANALYSIS_TYPES[type]['func'](self.audio['data'], self.audio['samplerate'], **params)
        params = fill_default_params(ANALYSIS_TYPES[type]['func'], params)
        print("params", params)
        for det in det_result:
            if isinstance(det, tuple):
                detection = Detection(start=det[0], end=det[1], type=type, params=params)
            else:
                detection = Detection(start=det, end=None, type=type, params=params)
            redis_conn.rpush(f"results:{self.audio_base}_{self.start_timestamp}", str(detection))
        self.complete(type)
        print("Found", len(det_result), type, "detections")
        print(redis_conn.llen(f"results:{self.audio_base}_{self.start_timestamp}"), "total detections for", self.audio_file, "so far")

    def complete(self, type : str):
        redis_conn = redis.from_url(self.redis_url)

        lua = """
        redis.call('HSET', KEYS[1], ARGV[1], 'completed')
        for i = 2, #ARGV do
            if redis.call('HGET', KEYS[1], ARGV[i]) ~= 'completed' then
                return 0
            end
        end
        return 1
        """

        result = redis_conn.eval(lua, 1, "job_status", f"{self.audio_base}_{type}_{self.start_timestamp}", *self.job_ids)

        if result != 1:
            return

        job_queue = Queue(connection=redis_conn)
        job_queue.enqueue(self.create_report)

    def create_report(self):
        redis_conn = redis.from_url(self.redis_url)
        print(f"Creating report for {self.audio_file}...")
        results = []

        while redis_conn.llen(f"results:{self.audio_base}_{self.start_timestamp}") > 0:
            det_str = redis_conn.lpop(f"results:{self.audio_base}_{self.start_timestamp}").decode('utf-8')
            print("dets:", det_str)
            detection = Detection.det_from_string(det_str)
            results.append(detection)
        
        # Convert Detection objects to dicts for JSON serialization
        results_dicts = [
            {
                "type": d.type,
                "start": d.start,
                "end": d.end,
                "params": d.params,
                "start_mmss": seconds_to_mmss(d.start),
                "end_mmss": seconds_to_mmss(d.end),
                "details": d.get_details()
            }
            for d in sorted(results)
        ]
        
        # Prepare output directory: detection_results/{audio_file_no_ext}_{timestamp}/
        ts_str = datetime.fromtimestamp(self.start_timestamp).strftime('%Y-%m-%d_%H-%M-%S')
        out_dir = os.path.join(OUTPUT_DIR, f"{self.audio_base}_{ts_str}")
        os.makedirs(out_dir, exist_ok=True)
        json_path = os.path.join(out_dir, f"{self.audio_base}_report.json")
        with open(json_path, 'w') as f:
            json.dump(results_dicts, f, indent=2)
        print("Report saved to:", out_dir)


def simulate_artifacts(loader : Type[AudioLoader], input_file: str, output_file: str, artifacts: dict, seed: int = 42):
    simulator = ArtifactSim(directory=loader.directory, artifacts=artifacts)
    simulator.distort_audio(input_file, output_file, seed=seed)

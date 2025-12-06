import os
import sys
import json
import traceback
import redis
from typing import Type
from rq import Queue
from datetime import datetime
import soundfile as sf

# Add src directory to path so imports work when RQ executes jobs
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from audio_processing.audio_import import AudioLoader
from audio_processing.utils import Detection, seconds_to_mmss, fill_default_params
from audio_processing.artifact_simulate import ArtifactSim
from .analysis_types import ANALYSIS_TYPES

# Use absolute path for output directory
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "detection_results")

class AudioDetectionJob:
    def __init__(self, loader: Type[AudioLoader], audio_file_path: str, redis_url: Type[str] = 'redis://localhost:6379/0', clip_pad: float = 0.1):
        self.redis_url = redis_url
        self.loader = loader
        self.completed = {}
        self.audio_file = audio_file_path
        self.audio = None
        self.job_ids = []
        self.audio_base = os.path.splitext(os.path.basename(self.audio_file))[0]
        self.start_timestamp = int(datetime.now().timestamp())
        self.clip_pad = clip_pad

        ts_str = datetime.fromtimestamp(self.start_timestamp).strftime('%Y-%m-%d_%H-%M-%S')
        self.out_dir = os.path.join(OUTPUT_DIR, f"{self.audio_base}_{ts_str}")
        os.makedirs(self.out_dir, exist_ok=True)

    def save_clip(self, det_type: str, id: int, start_s: float, end_s: float = None):
        if end_s is None:
            end_s = start_s  # Save a very short clip for point detections

        start = max(0, start_s - self.clip_pad)
        end = end_s + self.clip_pad

        start = int(start * self.audio['samplerate'])
        end = int(end * self.audio['samplerate'])

        os.makedirs(os.path.join(self.out_dir, "clips"), exist_ok=True)
        clip_path = os.path.join(self.out_dir, "clips", f"{det_type.lower()}-{id}.wav")

        sf.write(clip_path, self.audio['data'][start:end], self.audio['samplerate'])

    def load_and_queue(self, analyses: dict):
        try:
            redis_conn = redis.from_url(self.redis_url)
            job_queue = Queue(connection=redis_conn)
            
            print(f"Loading audio file: {self.audio_file}")
            self.audio = self.loader.load_audio_file(self.audio_file)

            for analysis_type in analyses.keys():
                self.job_ids.append(f"{self.audio_base}_{analysis_type}_{self.start_timestamp}")
                redis_conn.hset("job_status", f"{self.audio_base}_{analysis_type}_{self.start_timestamp}", "queued")

            print(f"Queueing detection jobs for: {self.audio_file}")
            for analysis_type, analysis_params in analyses.items():
                job_queue.enqueue(self.run_detection, analysis_type, analysis_params)
            return
        except Exception as e:
            print(f"[ERROR] Exception in load_and_queue: {e}")
            traceback.print_exc()
            raise  # Optionally re-raise to let RQ mark the job as failed
        
    def run_detection(self, det_type: str, params: dict):
        redis_conn = redis.from_url(self.redis_url)
        print(f"Running detection {det_type} on {self.audio_file}")
        
        params = fill_default_params(ANALYSIS_TYPES[det_type]['func'], params)
        
        det_result = ANALYSIS_TYPES[det_type]['func'](self.audio['data'], self.audio['samplerate'], **params)
        
        if ANALYSIS_TYPES[det_type]['type'] == 'in-file':
            for id, det in enumerate(det_result):
                if isinstance(det, tuple):
                    det = round(det[0], 3), round(det[1], 3)
                    self.save_clip(det_type, id=id, start_s=det[0], end_s=det[1])
                    detection = Detection(id=id, start=det[0], end=det[1], type=det_type, params=params)
                else:
                    det = round(det, 3)
                    self.save_clip(det_type, id=id, start_s=det)
                    detection = Detection(id=id, start=det, type=det_type, params=params, in_file=True)
                redis_conn.rpush(f"results:{self.audio_base}_{self.start_timestamp}", str(detection))
            
            print("Found", len(det_result), det_type, "detections")
            print(redis_conn.llen(f"results:{self.audio_base}_{self.start_timestamp}"), "total detections for", self.audio_file, "so far")
        else:
            detection = Detection(result=det_result, type=det_type, params=params, in_file=False)
            redis_conn.rpush(f"results:{self.audio_base}_{self.start_timestamp}", str(detection))
            
            print("Overall", det_type, "result:", str(detection))
            print("Completed", det_type, "analysis")
        
        self.complete(det_type)

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
        in_file_results = []
        overall_results = []

        while redis_conn.llen(f"results:{self.audio_base}_{self.start_timestamp}") > 0:
            det_str = redis_conn.lpop(f"results:{self.audio_base}_{self.start_timestamp}").decode('utf-8')
            detection = Detection.det_from_string(det_str)
            if detection.in_file:
                in_file_results.append(detection)
            else:
                overall_results.append(detection)
        
        # Convert Detection objects to dicts for JSON serialization
        overall_results = []
        overall_results.extend(
            [
                {
                    "type": "samplerate",
                    "params": {},
                    "result": self.audio['samplerate']
                },
                {
                    "type": "channels",
                    "params": {},
                    "result": self.audio['channels']
                },
                {
                    "type": "duration",
                    "params": {},
                    "result": seconds_to_mmss(self.audio['duration_sec'])
                }
            ]
        )
        overall_results.extend(
            [
                {
                    "type": d.type,
                    "params": d.params,
                    "result": d.result
                }
                for d in sorted(overall_results)
            ]
        )
        results_dicts = {
            "title": "AuQA Report for " + self.audio_file,
            "file": self.audio_file,
            "overall_results": overall_results,
            "in_file_detections": [
                {
                    "type": d.type,
                    "id": d.id,
                    "start": d.start,
                    "end": d.end,
                    "params": d.params,
                    "start_mmss": seconds_to_mmss(d.start),
                    "end_mmss": seconds_to_mmss(d.end),
                    "details": d.get_details()
                }
                for d in sorted(in_file_results)
            ]
        }

        # Prepare output directory: detection_results/{audio_file_no_ext}_{timestamp}/
        json_path = os.path.join(self.out_dir, f"{self.audio_base}_report.json")
        with open(json_path, 'w') as f:
            json.dump(results_dicts, f, indent=2)
        print("Report saved to:", self.out_dir)


def simulate_artifacts(loader : Type[AudioLoader], input_file: str, output_file: str, artifacts: dict, seed: int = 42):
    simulator = ArtifactSim(directory=loader.directory, artifacts=artifacts)
    simulator.distort_audio(input_file, output_file, seed=seed)

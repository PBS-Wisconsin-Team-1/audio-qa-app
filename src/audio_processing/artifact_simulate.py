import random
import numpy as np
from pydub import AudioSegment
from pydub.generators import WhiteNoise
import os

# Handle imports for both direct execution and module import
try:
    from . import audio_import
    AudioLoader = audio_import.AudioLoader
except ImportError:
    from audio_import import AudioLoader

AUDIO_DIR = os.path.join(".", "audio_files")

def seconds_to_mmss(seconds):
    """Convert seconds to mm:ss format"""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:05.2f}"

class ArtifactSim:
    def __init__(self, directory=AUDIO_DIR, artifacts: dict=None):
        self.loader = AudioLoader(directory=directory)
        self.artifacts = artifacts if artifacts else {'clicks': 2, 'pops': 2, 'cutouts': 2, 'clipping': 2}

    def insert_click(self, audio, position_ms, duration_ms=5, amplitude_reduction_db=10):
        """Insert a click sound (very short white noise) at position_ms"""
        click = WhiteNoise().to_audio_segment(duration=duration_ms).apply_gain(-amplitude_reduction_db)
        return audio.overlay(click, position=position_ms)

    def insert_pop(self, audio, position_ms, duration_ms=20, amplitude_reduction_db=5):
        """Insert a pop sound (short burst of white noise) at position_ms"""
        pop = WhiteNoise().to_audio_segment(duration=duration_ms).apply_gain(-amplitude_reduction_db)
        return audio.overlay(pop, position=position_ms)

    def insert_cutout(self, audio, position_ms, duration_ms=100):
        """Insert silent cutout at position_ms"""
        silence = AudioSegment.silent(duration=duration_ms)
        return audio[:position_ms] + silence + audio[position_ms + duration_ms:]

    def insert_clipping(self, audio, position_ms, duration_ms=50, clipping_level=0.7):
        """Simulate clipping by amplifying and then hard clipping the samples"""
        segment = audio[position_ms:position_ms+duration_ms]
        samples = np.array(segment.get_array_of_samples()).astype(np.float32)
        max_val = np.iinfo(segment.array_type).max
        
        # Amplify samples
        samples *= 2.0
        
        # Hard clip samples beyond clipping_level * max_val threshold
        clip_threshold = clipping_level * max_val
        samples = np.clip(samples, -clip_threshold, clip_threshold)
        
        # Convert back to audio segment
        clipped_segment = segment._spawn(samples.astype(segment.array_type).tobytes())
        return audio[:position_ms] + clipped_segment + audio[position_ms + duration_ms:]

    def distort_audio(self, input_file, output_file, seed=42):
        inserted_artifacts = []
        random.seed(seed)
        audio = self.loader.load_audio_file(input_file, type="pydub")['data']
        length_ms = len(audio)
        
        print(f"\n=== Inserting artifacts into {input_file} ===")
        
        # Insert clicks
        for i in range(self.artifacts['clicks']):
            pos = random.randint(0, length_ms - 10)
            audio = self.insert_click(audio, pos)
            timestamp = seconds_to_mmss(pos / 1000)
            print(f"Click #{i+1} at {timestamp}")
            inserted_artifacts.append(('click', pos / 1000))  # Store in seconds
        
        # Insert pops
        for i in range(self.artifacts['pops']):
            pos = random.randint(0, length_ms - 30)
            audio = self.insert_pop(audio, pos)
            timestamp = seconds_to_mmss(pos / 1000)
            print(f"Pop #{i+1} at {timestamp}")
            inserted_artifacts.append(('pop', pos / 1000))  # Store in seconds
        
        # Insert cutouts
        for i in range(self.artifacts['cutouts']):
            pos = random.randint(0, length_ms - 150)
            audio = self.insert_cutout(audio, pos)
            timestamp = seconds_to_mmss(pos / 1000)
            print(f"Cutout #{i+1} at {timestamp}")
            inserted_artifacts.append(('cutout', pos / 1000))  # Store in seconds
        
        # Insert clipping
        for i in range(self.artifacts['clipping']):
            pos = random.randint(0, length_ms - 60)
            audio = self.insert_clipping(audio, pos)
            timestamp = seconds_to_mmss(pos / 1000)
            print(f"Clipping #{i+1} at {timestamp}")
            inserted_artifacts.append(('clipping', pos / 1000))  # Store in seconds
        
        # Export distorted audio
        audio.export(os.path.join(self.loader.directory, output_file), format="wav")
        print(f"\n✓ Distorted audio saved to {output_file}")
        print(f"Total artifacts inserted: {len(inserted_artifacts)}\n")
        
        return inserted_artifacts

# run with python artifact_simulate.py input.wav output.wav [-d directory]
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python artifact_simulate.py input.wav output.wav [-d directory]")
        print("  -d directory: Optional path to audio files directory (default: ./audio_files)")
        exit(1)
    
    # Parse optional -d directory argument
    directory = AUDIO_DIR
    if len(sys.argv) > 3 and sys.argv[3] == '-d' and len(sys.argv) > 4:
        directory = sys.argv[4]
    
    aSim = ArtifactSim(directory=directory)
    aSim.distort_audio(sys.argv[1], sys.argv[2])
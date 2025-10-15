import random
import numpy as np
from pydub import AudioSegment
from pydub.generators import WhiteNoise

def insert_click(audio, position_ms, duration_ms=5, amplitude_reduction_db=10):
    """Insert a click sound (very short white noise) at position_ms"""
    click = WhiteNoise().to_audio_segment(duration=duration_ms).apply_gain(-amplitude_reduction_db)
    return audio.overlay(click, position=position_ms)

def insert_pop(audio, position_ms, duration_ms=20, amplitude_reduction_db=5):
    """Insert a pop sound (short burst of white noise) at position_ms"""
    pop = WhiteNoise().to_audio_segment(duration=duration_ms).apply_gain(-amplitude_reduction_db)
    return audio.overlay(pop, position=position_ms)

def insert_cutout(audio, position_ms, duration_ms=100):
    """Insert silent cutout at position_ms"""
    silence = AudioSegment.silent(duration=duration_ms)
    return audio[:position_ms] + silence + audio[position_ms + duration_ms:]

def insert_clipping(audio, position_ms, duration_ms=50, clipping_level=0.7):
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

def distort_audio(input_file, output_file, seed=42):
    random.seed(seed)
    audio = AudioSegment.from_file(input_file)
    length_ms = len(audio)
    
    # Insert clicks
    for _ in range(3):
        pos = random.randint(0, length_ms - 10)
        audio = insert_click(audio, pos)
    
    # Insert pops
    for _ in range(2):
        pos = random.randint(0, length_ms - 30)
        audio = insert_pop(audio, pos)
    
    # Insert cutouts
    for _ in range(2):
        pos = random.randint(0, length_ms - 150)
        audio = insert_cutout(audio, pos)
    
    # Insert clipping
    for _ in range(2):
        pos = random.randint(0, length_ms - 60)
        audio = insert_clipping(audio, pos)
    
    # Export distorted audio
    audio.export(output_file, format="wav")
    print(f"Distorted audio saved to {output_file}")

# run with python distort_audio.py input.wav output.wav
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python distort_audio.py input.wav output.wav")
    else:
        distort_audio(sys.argv[1], sys.argv[2])
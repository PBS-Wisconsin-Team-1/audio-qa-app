import os
import librosa
import numpy as np

# default location for audio files is in "audio-qa-app/audio_files"
AUDIO_DIR = os.path.join(".", "audio_files")

class AudioLoader:
    def __init__(self, directory=AUDIO_DIR, sr=22050, mono=True):
        self.directory = directory
        self.sr = sr
        self.mono = mono

    def load_all(self):
        """
        Loads all audio files in the given directory using librosa.
        Returns a dict mapping filename to numpy array and sample rate.
        """
        audio_data = {}
        print("Loading audio files from:", self.directory)
        for filename in os.listdir(self.directory):
            if filename.lower().endswith((".wav", ".flac", ".ogg", ".mp3", ".m4a")):
                audio_data[filename] = self.load_audio_file(filename)
        return audio_data

    def load_batch(self, filenames):
        """
        Loads a batch of audio files specified in the filenames list.
        Returns a dict mapping filename to numpy array and sample rate.
        """
        audio_data = {}
        for filename in filenames:
            if filename.lower().endswith((".wav", ".flac", ".ogg", ".mp3", ".m4a")):
                audio_data[filename] = self.load_audio_file(filename)
        return audio_data

    def load_audio_file(self, filename):
        """
        Loads a single audio file using librosa.
        """
        filepath = os.path.join(self.directory, filename)
        print("Loading:", filepath)
        try:
            data, samplerate = librosa.load(filepath, sr=self.sr, mono=self.mono)
            return {
                "data": data,
                "samplerate": samplerate
            }
        except Exception as e:
            print(f"Failed to load {filename}: {e}")
            return None

# Example usage
if __name__ == "__main__":
    audio_loader = AudioLoader()
    for name, info in audio_loader.audio_data.items():
        print(f"{name}: {info['data'].shape}, {info['samplerate']} Hz")
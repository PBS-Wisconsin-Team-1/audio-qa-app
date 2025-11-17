import os
import librosa
from pydub import AudioSegment

# default location for audio files is in "audio-qa-app/audio_files"
AUDIO_DIR = os.path.join("..", "audio_files")

class AudioLoader:
    def __init__(self, directory=AUDIO_DIR, sr=22050, mono=True):
        self.directory = directory
        self.sr = sr
        self.mono = mono

    def is_valid_audio_file(self, filename: str) -> bool:
        """
        Check if the file is a valid audio file based on its extension.
        """
        return filename in self.get_file_list()

    def get_file_list(self):
        """
        Returns a list of audio files in the given directory.
        """
        return [f for f in os.listdir(self.directory) if f.lower().endswith((".wav", ".flac", ".ogg", ".mp3", ".m4a"))]

    def load_all(self):
        """
        Loads all audio files in the given directory using librosa.
        Returns a dict mapping filename to numpy array and sample rate.
        """
        audio_data = {}
        print("Loading audio files from:", self.directory)
        for filename in self.get_file_list():
            audio_data[filename] = self.load_audio_file(filename)
        return audio_data

    def load_batch(self, filenames: list[str], type: str = "numpy") -> dict:
        """
        Loads a batch of audio files specified in the filenames list.
        Returns a dict mapping filename to numpy array and sample rate.
        """
        audio_data = {}
        for filename in filenames:
            audio_data[filename] = self.load_audio_file(filename, type=type)
        return audio_data

    def load_audio_file(self, filename: str, type: str = "numpy") -> dict:
        """
        Loads a single audio file using librosa.
        """
        filepath = os.path.join(self.directory, filename)
        print("Loading:", filepath)
        if self.is_valid_audio_file(filename):
            if type == "numpy":
                data, samplerate = librosa.load(filepath, sr=self.sr, mono=self.mono)
                return {
                    "data": data,
                    "samplerate": samplerate
                }
            elif type == "pydub":
                audio = AudioSegment.from_file(filepath)
                return {
                    "data": audio,
                    "samplerate": audio.frame_rate
                }
        else:
            print(f"Failed to load {filename}")

# Example usage
if __name__ == "__main__":
    audio_loader = AudioLoader()
    for name, info in audio_loader.audio_data.items():
        print(f"{name}: {info['data'].shape}, {info['samplerate']} Hz")
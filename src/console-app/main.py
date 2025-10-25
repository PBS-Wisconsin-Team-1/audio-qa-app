"""Console demo for audio_processing features.

Usage examples:
  python -m console_app.main list
  python -m console_app.main simulate ex5.wav ex5_distorted.wav --verbose
  python -m console_app.main detect ex5_distorted.wav
	python -m console_app.main visualize ex5.wav ex5_distorted.wav --plot

This small CLI shows how to load audio, run artifact simulation, run detectors,
and (optionally) plot waveforms for visual comparison.
"""

import argparse
import os
import sys
from typing import List

import matplotlib.pyplot as plt
import numpy as np

try:
	from audio_processing import audio_import, artifact_simulate, distortion_detection as dd
except Exception:
	# allow running from package root where src is on sys.path
	sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
	from audio_processing import audio_import, artifact_simulate, distortion_detection as dd

AUDIO_DIR = os.path.join("..", "..", "audio_files")
loader = audio_import.AudioLoader(directory=AUDIO_DIR)

def list_files() -> List[str]:
	files = loader.get_file_list()
	for f in files:
		print(f)
	return files


def detect(args):
	data = loader.load_audio_file(args.file)
	if data is None:
		print("Failed to load audio")
		return
	y = data['data']
	sr = data['samplerate']

	cutouts = dd.detect_cutout(y, sr, threshold=args.cut_thresh, min_silence_duration_ms=args.min_silence_ms)
    

	print(f"\nDetections for {args.file}:")

	if cutouts:
		print(" Cutout regions:")
		for s, e in cutouts:
			print(f"  - {s:.3f}s -> {e:.3f}s")
		T = len(y) / sr
		t = np.linspace(0, T, len(y))
		amp = np.max(np.abs(y))
		ymin, ymax = -1.05 * amp, 1.05 * amp
		plt.figure(figsize=(12, 4))
		plt.plot(t, y, color='steelblue', linewidth=0.6)
		for s, e in cutouts:
			plt.axvspan(s, e, color='purple', alpha=0.3, label='Cutout')
		plt.title(f'Waveform with detected artifacts: {args.file}')
		plt.ylim(ymin, ymax)
		plt.xlabel('Time (s)')
		plt.ylabel('Amplitude')
		if cutouts:
			handles = []
			handles.append(plt.Line2D([0], [0], color='purple', lw=6, alpha=0.3, label='Cutout'))
			plt.legend(handles=handles)
		plt.tight_layout()
		plt.show()
	else:
		print(" No cutouts detected.")

def simulate(args):
	"""Run artifact simulation (CLI wrapper).

	Expects args.input, args.output, args.seed, args.verbose
	"""
	aSim = artifact_simulate.ArtifactSim(directory=AUDIO_DIR)
	try:
		aSim.distort_audio(args.input, args.output, seed=getattr(args, 'seed', 42), verbose=getattr(args, 'verbose', False))
		print(f"Wrote distorted file: {args.output}")
	except Exception as e:
		print(f"Simulation failed: {e}")


def visualize(args):
    data = loader.load_audio_file(args.file)
    if data is None:
        print("Failed to load audio")
        return
    y = data['data']
    sr = data['samplerate']

    T = len(y) / sr
    t = np.linspace(0, T, len(y))
    amp = np.max(np.abs(y))
    ymin, ymax = -1.05 * amp, 1.05 * amp
    plt.figure(figsize=(12, 4))
    plt.plot(t, y, color='steelblue', linewidth=0.6)
    plt.title(f'Waveform: {args.file}')
    plt.ylim(ymin, ymax)
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.tight_layout()
    plt.show()


def build_parser():
	p = argparse.ArgumentParser(description="Console demo for audio_processing")
	sub = p.add_subparsers(dest='cmd')

	sp_list = sub.add_parser('list', help='List audio files in audio directory')

	sp_sim = sub.add_parser('simulate', help='Insert artifacts into an audio file')
	sp_sim.add_argument('input')
	sp_sim.add_argument('output')
	sp_sim.add_argument('--seed', type=int, default=42)
	sp_sim.add_argument('--verbose', action='store_true')

	sp_det = sub.add_parser('detect', help='Run detectors on a file and plot waveform with artifacts highlighted')
	sp_det.add_argument('file')
	sp_det.add_argument('--clip-thresh', dest='clip_thresh', type=float, default=0.98)
	sp_det.add_argument('--min-clip-ms', dest='min_clip_ms', type=int, default=10)
	sp_det.add_argument('--cut-thresh', dest='cut_thresh', type=float, default=0.01)
	sp_det.add_argument('--min-silence-ms', dest='min_silence_ms', type=int, default=20)

	sp_vis = sub.add_parser('visualize', help='Visualize a single waveform')
	sp_vis.add_argument('file')

	return p


def main(argv=None):
	# If argv is omitted (interactive), run a prompt loop. Otherwise parse CLI args.
	if argv is None:
		return interactive_loop()

	parser = build_parser()
	args = parser.parse_args(argv)
	if args.cmd is None:
		parser.print_help()
		return

	if args.cmd == 'list':
		list_files()
	elif args.cmd == 'simulate':
		simulate(args)
	elif args.cmd == 'detect':
		detect(args)
	elif args.cmd == 'visualize':
		visualize(args)



def interactive_loop():
	"""Simple interactive menu to exercise the package features.

	This uses the same helper functions as the CLI subcommands.
	"""

	print("Audio QA console — interactive mode")
	while True:
		print("\nChoose an action:")
		print("  1) List audio files")
		print("  2) Simulate artifacts (distort file)")
		print("  3) Run detectors on a file (with plot)")
		print("  4) Visualize a single waveform")
		print("  5) Quit")
		choice = input("Enter choice [1-5]: ").strip()
		if choice == '1':
			list_files()
		elif choice == '2':
			inp = input("Input filename (in audio dir): ").strip()
			out = input("Output filename: ").strip()
			seed = input("Seed (enter for 42): ").strip() or '42'
			verbose = input("Verbose? (y/n): ").strip().lower().startswith('y')
			class Args:
				pass
			a = Args()
			a.input = inp
			a.output = out
			a.seed = int(seed)
			a.verbose = verbose
			try:
				simulate(a)
			except Exception as e:
				print(f"Simulation failed: {e}")
		elif choice == '3':
			fname = input("Filename to detect on: ").strip()
			class Args:
				pass
			a = Args()
			a.file = fname
			a.cut_thresh = float(input("Cutout threshold (default 0.001): ").strip() or 0.001)
			a.min_silence_ms = int(input("Min silence ms (default 50): ").strip() or 50)
			try:
				detect(a)
			except Exception as e:
				print(f"Detection failed: {e}")
		elif choice == '4':
			fname = input("Filename to visualize: ").strip()
			class Args:
				pass
			a = Args()
			a.file = fname
			try:
				visualize(a)
			except Exception as e:
				print(f"Visualize failed: {e}")
		elif choice == '5' or choice.lower() in ('q', 'quit', 'exit'):
			print("Goodbye")
			break
		else:
			print("Invalid choice — enter 1-5")


if __name__ == '__main__':
	main()
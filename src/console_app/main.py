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
import numpy as np
import matplotlib.pyplot as plt
#import distortion_detector as ddist

try:
	from audio_processing import audio_import, artifact_simulate, distortion_detection as dd
except Exception:

	sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
	from audio_processing import audio_import, artifact_simulate, distortion_detection as dd

AUDIO_DIR = os.path.join("..", "..", "audio_files")
loader = audio_import.AudioLoader(directory=AUDIO_DIR)

def list_files() -> List[str]:
	files = loader.get_file_list()
	for f in files:
		print(f)
	return files

def detect(args, verbose=False):
	# Build full path for loading audio
	audio_path = os.path.join(loader.directory, args.file)
	
	# Load audio
	data = loader.load_audio_file(args.file)
	if data is None:
		print(f"Failed to load {audio_path}")
		return

	y = data['data']
	sr = data['samplerate']
	T = len(y) / sr
	t = np.linspace(0, T, len(y))
	amp = np.max(np.abs(y))
	ymin, ymax = -1.05 * amp, 1.05 * amp

	# Cutout detection
	cutouts = dd.detect_cutout(
		y, sr,
		threshold=getattr(args, 'cut_thresh', 0.001),
		min_len=getattr(args, 'min_silence_ms', 50)
	)

	# Distortion detection (full path)
	clip_thresh = getattr(args, 'clip_thresh', 0.98)
	dist_summary = dd.detect_clipping(
		y, sr, threshold=clip_thresh, summary=True
	)

	# Prepare distorted regions as (start, end) tuples
	if dist_summary:
		distorted_regions = dist_summary.get('distorted_regions_sec', [])
	else:
		distorted_regions = []

	# Print summaries
	if verbose:
		print(f"\nDetections for {args.file}:")
		if cutouts:
			print(" Cutout regions:")
			for s, e in cutouts:
				print(f"  - {s:.3f}s -> {e:.3f}s")
		else:
			print(" No cutouts detected.")

		if dist_summary:
			print(f"\nDistortion Detections for {args.file}:")
			print(f" Total Clipped Samples: {dist_summary.get('total_clipped_samples', 0)}")
			print(f" Clipping Detected in {dist_summary.get('clip_ratio', 0)*100:.4f}% of samples")
			print(f" Distorted Regions (first 10): {distorted_regions[:10]}")

	# Plot waveform with overlays
	plt.figure(figsize=(12,4))
	plt.plot(t, y, color='steelblue', linewidth=0.6)

	# Cutout regions
	for s, e in cutouts:
		plt.axvspan(s, e, color='purple', alpha=0.3, label='Cutout')

	# Clipping/distortion regions: support both (start,end) tuples and single timestamps
	for region in distorted_regions:
		if isinstance(region, (list, tuple)) and len(region) >= 2:
			rs, re = region[0], region[1]
		else:
			# fallback to a tiny span if only a single time is provided
			rs = float(region)
			re = rs + 0.001
		plt.axvspan(rs, re, color='red', alpha=0.3, label='Distortion')

	# Remove duplicate labels
	handles, labels = plt.gca().get_legend_handles_labels()
	by_label = dict(zip(labels, handles))
	plt.legend(by_label.values(), by_label.keys())

	plt.title(f'Waveform with artifacts: {args.file}')
	plt.ylim(ymin, ymax)
	plt.xlabel('Time (s)')
	plt.ylabel('Amplitude')
	plt.tight_layout()
	plt.show()


def simulate(args):
	"""Run artifact simulation (CLI wrapper).

	Expects args.input, args.output, args.seed, args.verbose
	"""
	aSim = artifact_simulate.ArtifactSim(directory=AUDIO_DIR)
	try:
		artifacts = aSim.distort_audio(args.input, args.output, seed=getattr(args, 'seed', 42), verbose=getattr(args, 'verbose', False))
		print(f"Wrote distorted file: {args.output}")
		# Plot the distorted file and overlay inserted artifacts (if any) in a background thread

		try:
			data = loader.load_audio_file(args.output)
			if data is None:
				print(f"Failed to load output file for plotting: {args.output}")
				return
			y = data['data']
			sr = data['samplerate']
			duration = len(y) / sr
			time_axis = np.linspace(0, duration, len(y))
			plt.figure(figsize=(12, 4))
			plt.plot(time_axis, y, alpha=0.7, linewidth=0.6, color='blue')

			# Highlight artifacts if available
			if artifacts:
				color_map = {
					'click': 'red',
					'pop': 'orange',
					'cutout': 'purple',
					'clipping': 'yellow'
				}
				for artifact in artifacts:
					if artifact is None:
						continue
					# Support tuple/list or dict
					if isinstance(artifact, (list, tuple)):
						a_type = artifact[0] if len(artifact) > 0 else 'artifact'
						timestamp = artifact[1] if len(artifact) > 1 else 0.0
						duration_ms = artifact[2] if len(artifact) > 2 else 10
					elif isinstance(artifact, dict):
						a_type = artifact.get('type', 'artifact')
						timestamp = artifact.get('timestamp', artifact.get('time', 0.0))
						duration_ms = artifact.get('duration_ms', artifact.get('duration', 10))
					else:
						# Unknown format; skip
						continue
					duration_sec = (duration_ms or 0) / 1000.0
					color = color_map.get(a_type, 'gray')
					plt.axvspan(timestamp, timestamp + duration_sec, color=color, alpha=0.3, label=a_type)

			plt.title(f"{args.output} waveform with simulated artifacts")
			plt.xlabel("Time (seconds)")
			plt.ylabel("Amplitude")
			plt.grid(True, alpha=0.3)
			handles, labels = plt.gca().get_legend_handles_labels()
			by_label = dict(zip(labels, handles))
			if by_label:
				plt.legend(by_label.values(), by_label.keys(), loc='upper right')
			plt.tight_layout()
			plt.show()
		except Exception as e:
			print(f"Error plotting simulated file: {e}")
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
			files = loader.get_file_list()
			if not files:
				print("No audio files found.")
				continue
			print("Select input file:")
			for i, f in enumerate(files):
				print(f"  {i+1}) {f}")
			inp_idx = input("Enter number: ").strip()
			try:
				inp = files[int(inp_idx)-1]
			except Exception:
				print("Invalid selection.")
				continue
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
			files = loader.get_file_list()
			if not files:
				print("No audio files found.")
				continue
			print("Select file to detect on:")
			for i, f in enumerate(files):
				print(f"  {i+1}) {f}")
			inp_idx = input("Enter number: ").strip()
			try:
				fname = files[int(inp_idx)-1]
			except Exception:
				print("Invalid selection.")
				continue
			class Args:
				pass
			a = Args()
			a.file = fname
			# Safely parse float/int with defaults
			try: a.cut_thresh = float(input("Cutout threshold (default 0.001): ").strip() or 0.001)
			except: a.cut_thresh = 0.001
			try: a.min_silence_ms = int(input("Min silence ms (default 50): ").strip() or 50)
			except: a.min_silence_ms = 50
			try: a.clip_thresh = float(input("Clip threshold (default 0.98): ").strip() or 0.98)
			except: a.clip_thresh = 0.98

			try:
				detect(a)
			except Exception as e:
				print(f"Detection failed: {e}")

		
		elif choice == '4':
			files = loader.get_file_list()
			if not files:
				print("No audio files found.")
				continue
			print("Select file to visualize:")
			for i, f in enumerate(files):
				print(f"  {i+1}) {f}")
			inp_idx = input("Enter number: ").strip()
			try:
				fname = files[int(inp_idx)-1]
			except Exception:
				print("Invalid selection.")
				continue
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
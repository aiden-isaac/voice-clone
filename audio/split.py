#!/usr/bin/env python3
"""
Smart WAV file splitter that creates segments of 5-15 seconds without cutting words.
Uses silence detection to find natural break points.
"""

import os
import glob
import subprocess
import json
import sys
from pathlib import Path

def get_audio_duration(file_path):
    """Get duration of audio file in seconds using ffprobe."""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-print_format', 'json', 
            '-show_format', file_path
        ], capture_output=True, text=True, check=True)
        
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except (subprocess.CalledProcessError, KeyError, ValueError) as e:
        print(f"Error getting duration for {file_path}: {e}")
        return None

def detect_silence_points(file_path, min_silence_duration=0.3, silence_threshold=-40):
    """Detect silence points in audio file using ffmpeg silencedetect filter."""
    try:
        result = subprocess.run([
            'ffmpeg', '-i', file_path, '-af', 
            f'silencedetect=noise={silence_threshold}dB:d={min_silence_duration}',
            '-f', 'null', '-'
        ], capture_output=True, text=True)
        
        # Parse silence detection output
        silence_starts = []
        silence_ends = []
        
        for line in result.stderr.split('\n'):
            if 'silence_start:' in line:
                try:
                    start_time = float(line.split('silence_start: ')[1].split()[0])
                    silence_starts.append(start_time)
                except (IndexError, ValueError):
                    continue
            elif 'silence_end:' in line:
                try:
                    end_time = float(line.split('silence_end: ')[1].split()[0])
                    silence_ends.append(end_time)
                except (IndexError, ValueError):
                    continue
        
        # Combine silence periods (use end times as potential cut points)
        return silence_ends
    except subprocess.CalledProcessError as e:
        print(f"Error detecting silence in {file_path}: {e}")
        return []

def find_optimal_cut_points(duration, silence_points, min_segment=5, max_segment=15):
    """Find optimal cut points based on silence detection and segment length constraints."""
    if duration <= max_segment:
        return []  # No need to split
    
    cut_points = [0]  # Start with beginning
    current_start = 0
    
    while current_start < duration:
        # Find the ideal end point (between min and max segment length)
        ideal_end = current_start + max_segment
        min_end = current_start + min_segment
        
        if ideal_end >= duration:
            # Last segment
            break
        
        # Find the best silence point between min_end and ideal_end
        best_cut = None
        for silence_point in silence_points:
            if min_end <= silence_point <= ideal_end:
                best_cut = silence_point
            elif silence_point > ideal_end:
                break
        
        if best_cut is None:
            # No silence found in ideal range, look for closest silence after min_end
            for silence_point in silence_points:
                if silence_point > min_end:
                    best_cut = silence_point
                    break
            
            # If still no silence found, cut at max_segment length
            if best_cut is None:
                best_cut = ideal_end
        
        cut_points.append(best_cut)
        current_start = best_cut
    
    return cut_points[1:]  # Remove the initial 0

def split_audio_file(input_file, cut_points, output_dir):
    """Split audio file at specified cut points."""
    file_stem = Path(input_file).stem
    
    # Create segments
    start_time = 0
    segment_num = 0
    
    for i, end_time in enumerate(cut_points + [None]):  # Add None for last segment
        output_file = os.path.join(output_dir, f"split_{file_stem}_{segment_num:03d}.wav")
        
        if end_time is None:
            # Last segment - go to end of file
            cmd = [
                'ffmpeg', '-i', input_file, '-ss', str(start_time),
                '-c', 'copy', output_file, '-y'
            ]
        else:
            # Regular segment
            duration = end_time - start_time
            cmd = [
                'ffmpeg', '-i', input_file, '-ss', str(start_time),
                '-t', str(duration), '-c', 'copy', output_file, '-y'
            ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"Created: {output_file} ({end_time - start_time if end_time else 'remaining'}s)")
        except subprocess.CalledProcessError as e:
            print(f"Error creating segment {output_file}: {e}")
        
        if end_time is None:
            break
            
        start_time = end_time
        segment_num += 1

def main():
    # Create output directory if it doesn't exist
    output_dir = "./wav"
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all WAV files in current directory
    wav_files = glob.glob("*.wav")
    
    if not wav_files:
        print("No WAV files found in current directory.")
        return
    
    print(f"Found {len(wav_files)} WAV file(s) to process.")
    
    for wav_file in wav_files:
        print(f"\nProcessing: {wav_file}")
        
        # Get audio duration
        duration = get_audio_duration(wav_file)
        if duration is None:
            continue
        
        print(f"Duration: {duration:.2f} seconds")
        
        # If file is already short enough, just copy it
        if duration <= 15:
            file_stem = Path(wav_file).stem
            output_file = os.path.join(output_dir, f"split_{file_stem}_000.wav")
            try:
                subprocess.run(['cp', wav_file, output_file], check=True)
                print(f"Copied (no split needed): {output_file}")
            except subprocess.CalledProcessError:
                print(f"Error copying {wav_file}")
            continue
        
        # Detect silence points
        print("Detecting silence points...")
        silence_points = detect_silence_points(wav_file)
        print(f"Found {len(silence_points)} silence points")
        
        # Find optimal cut points
        cut_points = find_optimal_cut_points(duration, silence_points)
        print(f"Cut points: {cut_points}")
        
        # Split the file
        split_audio_file(wav_file, cut_points, output_dir)
    
    print("\nProcessing complete!")

if __name__ == "__main__":
    # Check if required tools are available
    for tool in ['ffmpeg', 'ffprobe']:
        try:
            subprocess.run([tool, '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"Error: {tool} is not installed or not in PATH")
            sys.exit(1)
    
    main()

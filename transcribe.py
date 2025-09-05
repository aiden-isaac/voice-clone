import os
import whisper

# Initialize Whisper model (you can choose between 'tiny', 'base', 'small', 'medium', 'large')
model = whisper.load_model("medium")

# Path to the directory containing the audio files
audio_dir = "./audio/wav"
output_csv = "./audio/metadata.csv"

# List all .wav files in the directory
audio_files = [f for f in os.listdir(audio_dir) if f.endswith(".wav")]
audio_files.sort()  # Sort the files alphabetically (optional)

# Open the CSV file for writing
with open(output_csv, "w") as f:
    for audio_file in audio_files:
        # Full path to the audio file
        audio_path = os.path.join(audio_dir, audio_file)

        # Transcribe the audio file
        result = model.transcribe(audio_path)

        # Extract the transcription text
        transcription = result["text"].strip()

        # Write the filename (without .wav extension) and transcription to the CSV
        file_id = os.path.splitext(audio_file)[0]  # Get file name without extension
        f.write(f"{file_id}|{transcription}\n")

print(f"Transcriptions complete! Metadata saved to {output_csv}")


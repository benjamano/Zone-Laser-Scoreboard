import sounddevice as sd
import numpy as np
import librosa

device_index = 57  

print(sd.query_devices())

SAMPLE_RATE = 48000
BUFFER_DURATION = 1 

audio_buffer = np.zeros(int(SAMPLE_RATE * BUFFER_DURATION), dtype=np.float32)

def calculate_bpm(audio_data, sr):
    onset_env = librosa.onset.onset_strength(y=audio_data, sr=sr)
    tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
    return tempo

# Callback function for audio capture
def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    # Update the rolling buffer with new audio data
    global audio_buffer
    audio_buffer = np.roll(audio_buffer, -frames)
    

    audio_buffer[-frames:] = np.mean(indata, axis=1)

    # Calculate BPM from the buffer
    bpm = calculate_bpm(audio_buffer, SAMPLE_RATE)
    print(f"BPM: {bpm}")

# Start capturing audio from the output device
while True:
    with sd.InputStream(samplerate=SAMPLE_RATE, device=device_index, channels=2, callback=audio_callback, dtype='float32'):
        sd.sleep(120000)

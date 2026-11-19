import wave
import numpy as np
import sounddevice as sd

def jouer(chemin):
    """Joue un .wav 16 bits et attend la fin de la lecture."""

    with wave.open(chemin, "rb") as wf:
        channels = wf.getnchannels()
        sample_rate = wf.getframerate()  # lu dans le fichier (44000 Hz pour l'encodeur)
        sample_width = wf.getsampwidth()
        frames = wf.readframes(wf.getnframes())

    if sample_width != 2:
        raise ValueError("Le fichier doit être en 16 bits (int16), comme écrit par l'encodeur")

    audio_data = np.frombuffer(frames, dtype="<i2")
    if channels > 1:
        audio_data = audio_data.reshape(-1, channels)

    print(f"Lecture de {chemin} : {sample_rate} Hz, {len(audio_data) / sample_rate:.2f} s")
    sd.play(audio_data, samplerate=sample_rate)
    sd.wait()  # attend la fin de la lecture
    print("Lecture terminée.")
import wave
import threading
import numpy as np
import sounddevice as sd
import nettoyer

SAMPLE_RATE = 44000  # Fréquence d'échantillonnage (Hz)
CHANNELS = 1         # 1 = mono, 2 = stéréo
DURATION = 60        # Durée maximale en secondes
OUTPUT_FILE = "messages/enregistrement.wav"

def enregistrer():
    print(f"Appuyez sur Entrée pour arrêter (maximum {DURATION} secondes).")

    chunks = []
    stop_event = threading.Event()

    def record_chunk(indata, frames, time, status):
        if status:
            print(status)
        chunks.append(indata.copy())

    def wait_for_enter():
        input()
        stop_event.set()

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        callback=record_chunk,
    )

    stream.start()
    threading.Thread(target=wait_for_enter, daemon=True).start()
    stop_event.wait(DURATION)
    stream.stop()
    stream.close()

    if not chunks:
        print("Aucun son enregistré.")
        return

    audio_data = np.concatenate(chunks, axis=0)[:int(DURATION * SAMPLE_RATE)]
    print("Enregistrement terminé.")

    with wave.open(OUTPUT_FILE, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 2 octets = 16 bits (correspond à int16)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())
    print(f"Fichier sauvegardé : {OUTPUT_FILE}")

    # filtre + recalage pour le décodeur (fichier laissé intact si aucun son n'est détecté)
    nettoyer.nettoyer(OUTPUT_FILE)

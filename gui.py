#!/usr/bin/env python3

import threading
import wave
from queue import Queue, Empty
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

import numpy as np
import sounddevice as sd

import decoder
import encoder
import jouer


BASE_DIR = Path(__file__).resolve().parent
MESSAGES_DIR = BASE_DIR / "messages"
MESSAGE_FILE = MESSAGES_DIR / "message.wav"
RECORDING_FILE = MESSAGES_DIR / "enregistrement.wav"

SAMPLE_RATE = 44100
CHANNELS = 1
MAX_RECORDING_SECONDS = 60


class SignalGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Encodeur / Decodeur M-FSK")
        self.geometry("720x520")
        self.minsize(620, 450)

        self.valence = tk.StringVar(value="4")
        self.source = tk.StringVar(value="message")
        self.recording_stop = None
        self.recording_thread = None
        self.recording_active = False
        self.recording_peak = 0
        self.recording_status = Queue()
        self.input_devices = {}
        self.input_device_error = None
        self._load_input_devices()

        self._create_widgets()

    def _load_input_devices(self):
        try:
            devices = sd.query_devices()
            host_apis = sd.query_hostapis()
            for index, device in enumerate(devices):
                if device["max_input_channels"] < 1:
                    continue
                host = host_apis[device["hostapi"]]["name"]
                label = f'{index}: {device["name"]} ({host})'
                self.input_devices[label] = (
                    index,
                    int(round(device["default_samplerate"])),
                )
        except Exception as exc:
            self.input_device_error = str(exc)

    def _create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        encode_tab = ttk.Frame(notebook, padding=15)
        decode_tab = ttk.Frame(notebook, padding=15)
        play_tab = ttk.Frame(notebook, padding=15)
        record_tab = ttk.Frame(notebook, padding=15)

        notebook.add(encode_tab, text="Encoder")
        notebook.add(decode_tab, text="Decoder")
        notebook.add(play_tab, text="Jouer")
        notebook.add(record_tab, text="Enregistrer")

        ttk.Label(encode_tab, text="Texte a encoder :").pack(anchor="w")
        self.text_entry = tk.Text(encode_tab, height=7, wrap="word")
        self.text_entry.pack(fill="x", pady=(5, 10))

        options = ttk.Frame(encode_tab)
        options.pack(fill="x")
        ttk.Label(options, text="Valence :").pack(side="left")
        ttk.Combobox(
            options,
            textvariable=self.valence,
            values=("2", "4", "8", "16", "32"),
            state="readonly",
            width=8,
        ).pack(side="left", padx=(5, 15))
        ttk.Button(options, text="Encoder", command=self.encode_message).pack(
            side="right"
        )

        ttk.Label(decode_tab, text="Source :").pack(anchor="w")
        source_row = ttk.Frame(decode_tab)
        source_row.pack(fill="x", pady=5)
        ttk.Radiobutton(
            source_row,
            text="messages/message.wav",
            variable=self.source,
            value="message",
        ).pack(side="left")
        ttk.Radiobutton(
            source_row,
            text="messages/enregistrement.wav",
            variable=self.source,
            value="recording",
        ).pack(side="left", padx=15)
        ttk.Button(source_row, text="Decoder", command=self.decode_message).pack(
            side="right"
        )

        ttk.Label(play_tab, text="Fichier a jouer :").pack(anchor="w")
        play_row = ttk.Frame(play_tab)
        play_row.pack(fill="x", pady=5)
        ttk.Radiobutton(
            play_row,
            text="Message",
            variable=self.source,
            value="message",
        ).pack(side="left")
        ttk.Radiobutton(
            play_row,
            text="Enregistrement",
            variable=self.source,
            value="recording",
        ).pack(side="left", padx=15)
        ttk.Button(play_row, text="Jouer", command=self.play_message).pack(
            side="right"
        )

        ttk.Label(
            record_tab,
            text=f"Enregistrement mono, {MAX_RECORDING_SECONDS} secondes maximum.",
        ).pack(anchor="w", pady=(0, 10))
        device_row = ttk.Frame(record_tab)
        device_row.pack(fill="x", pady=(0, 10))
        ttk.Label(device_row, text="Microphone :").pack(side="left")
        self.input_device = tk.StringVar()
        device_labels = list(self.input_devices)
        default_input = sd.default.device[0]
        default_label = next(
            (
                label
                for label, (index, _) in self.input_devices.items()
                if index == default_input
            ),
            device_labels[0] if device_labels else "",
        )
        self.input_device.set(default_label)
        self.input_device_combo = ttk.Combobox(
            device_row,
            textvariable=self.input_device,
            values=device_labels,
            state="readonly",
            width=55,
        )
        self.input_device_combo.pack(side="left", fill="x", expand=True, padx=5)

        record_row = ttk.Frame(record_tab)
        record_row.pack(fill="x")
        self.record_button = ttk.Button(
            record_row, text="Commencer", command=self.start_recording
        )
        self.record_button.pack(side="left")
        self.stop_button = ttk.Button(
            record_row,
            text="Arreter",
            command=self.stop_recording,
            state="disabled",
        )
        self.stop_button.pack(side="left", padx=5)
        self.recording_level = ttk.Progressbar(
            record_tab, maximum=32767, mode="determinate"
        )
        self.recording_level.pack(fill="x", pady=(15, 2))
        self.recording_status_label = ttk.Label(
            record_tab, text="Niveau du microphone : inactif"
        )
        self.recording_status_label.pack(anchor="w")

        ttk.Label(self, text="Resultats").pack(anchor="w", padx=12)
        self.output = tk.Text(self, height=8, wrap="word", state="disabled")
        self.output.pack(fill="both", expand=False, padx=10, pady=(5, 10))

    def append_output(self, text):
        self.output.configure(state="normal")
        self.output.insert("end", text.rstrip() + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def clear_output(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def encode_message(self):
        texte = self.text_entry.get("1.0", "end-1c")
        if not texte:
            messagebox.showerror("Erreur", "Le texte est vide.")
            return
        if len(texte) > 128:
            messagebox.showerror(
                "Erreur", "Le texte doit contenir au plus 128 caracteres."
            )
            return
        if any(ord(c) > 255 for c in texte):
            messagebox.showerror(
                "Erreur",
                "Le texte contient un caractere qui ne tient pas sur 8 bits.",
            )
            return

        try:
            valence = int(self.valence.get())
            k = encoder.bits_par_symbole(valence)
            texte_binaire = encoder.transformationascii(texte)
            audio = encoder.creation_array(texte_binaire, valence, k)
            fichier = encoder.array_vers_wav(audio)
            frequences = np.linspace(encoder.Fmin, encoder.Fmax, valence)

            self.clear_output()
            self.append_output("Texte binaire : " + " ".join(texte_binaire))
            self.append_output("Frequences (Hz) : " + str(frequences))
            self.append_output(
                f"{fichier} : {len(audio)} echantillons, "
                f"{len(audio) / encoder.fs:.1f} s"
            )
        except Exception as exc:
            messagebox.showerror("Erreur d'encodage", str(exc))

    def decode_message(self):
        try:
            valence = int(self.valence.get())
        except ValueError:
            messagebox.showerror("Erreur de decodage", "Choisissez une valence valide.")
            return
        fichier = MESSAGE_FILE if self.source.get() == "message" else RECORDING_FILE

        def run():
            try:
                texte = decoder.decoder(str(fichier), valence)
                self.after(
                    0,
                    lambda: (
                        self.clear_output(),
                        self.append_output("Texte decode : " + texte),
                    ),
                )
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Erreur de decodage", str(exc)))

        threading.Thread(target=run, daemon=True).start()

    def play_message(self):
        fichier = MESSAGE_FILE if self.source.get() == "message" else RECORDING_FILE
        if not fichier.is_file():
            messagebox.showerror("Erreur", f"Fichier introuvable : {fichier}")
            return

        def run():
            try:
                jouer.jouer(str(fichier))
                self.after(0, lambda: self.append_output("Lecture terminee."))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Erreur de lecture", str(exc)))

        threading.Thread(target=run, daemon=True).start()

    def start_recording(self):
        if self.recording_thread and self.recording_thread.is_alive():
            return
        if not self.input_devices:
            messagebox.showerror(
                "Erreur d'enregistrement",
                self.input_device_error or "Aucun microphone d'entree n'est disponible.",
            )
            return

        chunks = []
        device_label = self.input_device.get()
        if device_label not in self.input_devices:
            messagebox.showerror(
                "Erreur d'enregistrement", "Choisissez un microphone valide."
            )
            return
        device_index, sample_rate = self.input_devices[device_label]

        def callback(indata, frames, time, status):
            if status:
                self.recording_status.put(str(status))
            self.recording_peak = int(np.max(np.abs(indata.astype(np.int32))))
            chunks.append(indata.copy())

        try:
            stream = sd.InputStream(
                device=device_index,
                samplerate=sample_rate,
                channels=CHANNELS,
                dtype="int16",
                callback=callback,
            )
            stream.start()
        except Exception as exc:
            messagebox.showerror("Erreur d'enregistrement", str(exc))
            return

        self.recording_stop = threading.Event()
        self.recording_peak = 0
        self.recording_active = True
        self.record_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.recording_status_label.configure(
            text=f"Enregistrement en cours sur {device_label} ({sample_rate} Hz)"
        )
        self.append_output(f"Enregistrement en cours : {device_label}")
        self.after(100, self._refresh_recording_status)

        def finish():
            self.recording_stop.wait(MAX_RECORDING_SECONDS)
            error = None
            result = None
            try:
                stream.stop()
                if chunks:
                    audio_data = np.concatenate(chunks, axis=0)
                    audio_data = audio_data[:MAX_RECORDING_SECONDS * sample_rate]
                    peak = int(np.max(np.abs(audio_data.astype(np.int32))))
                    MESSAGES_DIR.mkdir(parents=True, exist_ok=True)
                    with wave.open(str(RECORDING_FILE), "wb") as wf:
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(2)
                        wf.setframerate(sample_rate)
                        wf.writeframes(audio_data.tobytes())
                    if peak <= 2:
                        result = (
                            "Enregistrement presque silencieux. Verifiez le "
                            "microphone selectionne, son volume et les permissions."
                        )
                    else:
                        result = (
                            f"Enregistrement sauvegarde : {RECORDING_FILE} "
                            f"({len(audio_data) / sample_rate:.1f} s)"
                        )
                else:
                    error = "Aucune trame audio recue du microphone."
            except Exception as exc:
                error = str(exc)
            finally:
                try:
                    stream.close()
                except Exception as exc:
                    error = f"{error}; fermeture du flux : {exc}" if error else str(exc)

            self.after(0, lambda: self._recording_finished(result, error))

        self.recording_thread = threading.Thread(target=finish, daemon=True)
        self.recording_thread.start()

    def _refresh_recording_status(self):
        self.recording_level.configure(value=self.recording_peak)
        self.recording_status_label.configure(
            text=f"Niveau du microphone : {self.recording_peak} / 32767"
        )
        while True:
            try:
                self.append_output("Audio : " + self.recording_status.get_nowait())
            except Empty:
                break
        if self.recording_active:
            self.after(100, self._refresh_recording_status)

    def _recording_finished(self, result, error):
        self.recording_active = False
        self.record_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.recording_level.configure(value=0)
        if error:
            self.recording_status_label.configure(text="Erreur d'enregistrement.")
            messagebox.showerror("Erreur d'enregistrement", error)
            return
        self.recording_status_label.configure(text="Enregistrement termine.")
        self.append_output(result)
        if result and result.startswith("Enregistrement presque silencieux"):
            messagebox.showwarning("Enregistrement silencieux", result)

    def stop_recording(self):
        if self.recording_stop:
            self.recording_stop.set()


if __name__ == "__main__":
    app = SignalGui()
    app.mainloop()

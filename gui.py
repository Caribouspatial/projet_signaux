#!/usr/bin/env python3

import os
import threading
import tkinter as tk
import wave
from tkinter import filedialog, messagebox, ttk

import numpy as np
import sounddevice as sd
from scipy.io import wavfile

import decoder
import encoder
import enregistrer
import jouer
import nettoyer


DOSSIER_BASE = os.path.dirname(os.path.abspath(__file__))
DOSSIER_MESSAGES = os.path.join(DOSSIER_BASE, "messages")
FICHIER_MESSAGE = os.path.join(DOSSIER_MESSAGES, "message.wav")
FICHIER_ENREGISTREMENT = os.path.join(DOSSIER_MESSAGES, "enregistrement.wav")
VALENCES = ("2", "4", "8", "16", "32")


class SignauxGUI:
    def __init__(self, root):
        app = self
        app.root = root
        root.title("Projet signaux - M-FSK")
        root.geometry("760x620")
        root.minsize(700, 560)

        app.stop_recording_event = threading.Event()
        app.recording_thread = None

        style = ttk.Style(root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        app._creer_onglet_encoder(notebook)
        app._creer_onglet_decoder(notebook)
        app._creer_onglet_lecture(notebook)
        app._creer_onglet_enregistrement(notebook)

        app.status = tk.StringVar(value="Pret")
        ttk.Label(root, textvariable=app.status, relief="sunken", anchor="w").pack(
            fill="x", padx=10, pady=(0, 8)
        )

    def _cadre(self, parent):
        cadre = ttk.Frame(parent, padding=12)
        cadre.pack(fill="both", expand=True)
        return cadre

    def _creer_onglet_encoder(app, notebook):
        cadre = app._cadre(notebook)
        notebook.add(cadre, text="Encoder")

        ttk.Label(cadre, text="Texte a encoder :").grid(row=0, column=0, sticky="w")
        app.texte_encode = tk.Text(cadre, height=5, width=70)
        app.texte_encode.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(4, 12))

        ttk.Label(cadre, text="Valence :").grid(row=2, column=0, sticky="w")
        app.valence_encode = ttk.Combobox(
            cadre, values=VALENCES, state="readonly", width=10
        )
        app.valence_encode.set("4")
        app.valence_encode.grid(row=2, column=1, sticky="w")

        ttk.Button(cadre, text="Encoder", command=app.encoder_message).grid(
            row=2, column=2, sticky="e"
        )

        ttk.Label(cadre, text="Resultat :").grid(row=3, column=0, sticky="w", pady=(12, 4))
        app.resultat_encode = tk.Text(cadre, height=12, width=70, state="disabled")
        app.resultat_encode.grid(row=4, column=0, columnspan=3, sticky="nsew")

        cadre.columnconfigure(0, weight=1)
        cadre.rowconfigure(4, weight=1)

    def _creer_onglet_decoder(app, notebook):
        cadre = app._cadre(notebook)
        notebook.add(cadre, text="Decoder")

        ttk.Label(cadre, text="Fichier WAV :").grid(row=0, column=0, sticky="w")
        app.fichier_decode = tk.StringVar(value="message.wav")
        app.source_decode = ttk.Combobox(
            cadre,
            textvariable=app.fichier_decode,
            values=("message.wav", "enregistrement.wav"),
            width=35,
        )
        app.source_decode.grid(row=1, column=0, sticky="ew")
        ttk.Button(cadre, text="Choisir...", command=app.choisir_fichier_decode).grid(
            row=1, column=1, padx=(8, 0)
        )

        ttk.Label(cadre, text="Valence :").grid(row=2, column=0, sticky="w", pady=(12, 0))
        app.valence_decode = ttk.Combobox(
            cadre, values=VALENCES, state="readonly", width=10
        )
        app.valence_decode.set("4")
        app.valence_decode.grid(row=3, column=0, sticky="w")
        ttk.Button(cadre, text="Decoder", command=app.decoder_message).grid(
            row=3, column=1, sticky="e"
        )

        ttk.Label(cadre, text="Texte decode :").grid(row=4, column=0, sticky="w", pady=(12, 4))
        app.resultat_decode = tk.Text(cadre, height=12, width=70, state="disabled")
        app.resultat_decode.grid(row=5, column=0, columnspan=2, sticky="nsew")
        cadre.columnconfigure(0, weight=1)
        cadre.rowconfigure(5, weight=1)

    def _creer_onglet_lecture(app, notebook):
        cadre = app._cadre(notebook)
        notebook.add(cadre, text="Lire")

        ttk.Label(cadre, text="Fichier WAV :").grid(row=0, column=0, sticky="w")
        app.fichier_lecture = tk.StringVar(value="message.wav")
        app.source_lecture = ttk.Combobox(
            cadre,
            textvariable=app.fichier_lecture,
            values=("message.wav", "enregistrement.wav"),
            width=35,
        )
        app.source_lecture.grid(row=1, column=0, sticky="ew")
        ttk.Button(cadre, text="Choisir...", command=app.choisir_fichier_lecture).grid(
            row=1, column=1, padx=(8, 0)
        )
        ttk.Button(cadre, text="Lire", command=app.jouer_message).grid(
            row=2, column=0, pady=12, sticky="w"
        )
        cadre.columnconfigure(0, weight=1)

    def _creer_onglet_enregistrement(app, notebook):
        cadre = app._cadre(notebook)
        notebook.add(cadre, text="Enregistrer")

        ttk.Label(
            cadre,
            text="Enregistre jusqu'a 60 secondes dans messages/enregistrement.wav.",
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        app.bouton_enregistrer = ttk.Button(
            cadre, text="Demarrer l'enregistrement", command=app.demarrer_enregistrement
        )
        app.bouton_enregistrer.grid(row=1, column=0, pady=16, sticky="w")
        app.bouton_arreter = ttk.Button(
            cadre, text="Arreter", command=app.arreter_enregistrement, state="disabled"
        )
        app.bouton_arreter.grid(row=1, column=1, pady=16, padx=8, sticky="w")
        cadre.columnconfigure(0, weight=1)

    def _texte_resultat(app, widget, texte):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", texte)
        widget.configure(state="disabled")

    def _chemin_choisi(app, valeur):
        if os.path.isabs(valeur):
            return valeur
        return os.path.join(DOSSIER_MESSAGES, valeur)

    def choisir_fichier_decode(app):
        chemin = filedialog.askopenfilename(
            title="Choisir un fichier WAV",
            filetypes=[("Fichiers WAV", "*.wav"), ("Tous les fichiers", "*.*")],
            initialdir=DOSSIER_MESSAGES,
        )
        if chemin:
            app.fichier_decode.set(chemin)

    def choisir_fichier_lecture(app):
        chemin = filedialog.askopenfilename(
            title="Choisir un fichier WAV",
            filetypes=[("Fichiers WAV", "*.wav"), ("Tous les fichiers", "*.*")],
            initialdir=DOSSIER_MESSAGES,
        )
        if chemin:
            app.fichier_lecture.set(chemin)

    def lancer_tache(app, fonction, debut=None):
        if debut:
            app.status.set(debut)

        def travail():
            try:
                fonction()
            except Exception as erreur:
                app.root.after(
                    0,
                    lambda erreur=erreur: (
                        app.status.set("Erreur"),
                        messagebox.showerror("Erreur", str(erreur)),
                    ),
                )

        threading.Thread(target=travail, daemon=True).start()

    def encoder_message(app):
        texte = app.texte_encode.get("1.0", "end-1c")
        if not texte:
            messagebox.showerror("Erreur", "Le texte a encoder ne peut pas etre vide.")
            return
        if len(texte) > 128:
            messagebox.showerror("Erreur", "Le texte ne peut pas depasser 128 caracteres.")
            return
        if any(ord(c) > 255 for c in texte):
            messagebox.showerror(
                "Erreur",
                "Chaque caractere doit tenir sur 8 bits.",
            )
            return

        valence = int(app.valence_encode.get())

        def travail():
            k = encoder.bits_par_symbole(valence)
            texte_binaire = encoder.transformationascii(texte)
            audio = encoder.creation_array(texte_binaire, valence, k)
            chemin = encoder.array_vers_wav(audio)
            frequences = np.linspace(encoder.Fmin, encoder.Fmax, valence)
            resultat = (
                "Texte en binaire :\n"
                + " ".join(texte_binaire)
                + f"\n\nValence : {valence}\n"
                + f"k : {k} bits/symbole\n"
                + "Frequences (Hz) :\n"
                + ", ".join(f"{frequence:.1f}" for frequence in frequences)
                + f"\n\nFichier : {chemin}\n"
                + f"Longueur : {len(audio)} echantillons, {len(audio) / encoder.fs:.1f} s"
            )
            app.root.after(
                0,
                lambda: (
                    app._texte_resultat(app.resultat_encode, resultat),
                    app.status.set("Encodage termine"),
                ),
            )

        app.lancer_tache(travail, "Encodage en cours...")

    def decoder_message(app):
        valeur = app.fichier_decode.get()
        chemin = app._chemin_choisi(valeur)
        if not os.path.isfile(chemin):
            messagebox.showerror("Erreur", f"Fichier introuvable : {chemin}")
            return
        valence = int(app.valence_decode.get())

        def travail():
            texte = decoder.decoder(chemin, valence)
            app.root.after(
                0,
                lambda: (
                    app._texte_resultat(app.resultat_decode, texte),
                    app.status.set("Decodage termine"),
                ),
            )

        app.lancer_tache(travail, "Decodage en cours...")

    def jouer_message(app):
        valeur = app.fichier_lecture.get()
        chemin = app._chemin_choisi(valeur)
        if not os.path.isfile(chemin):
            messagebox.showerror("Erreur", f"Fichier introuvable : {chemin}")
            return

        def travail():
            jouer.jouer(chemin)
            app.root.after(0, lambda: app.status.set("Lecture terminee"))

        app.lancer_tache(travail, "Lecture en cours...")

    def demarrer_enregistrement(app):
        app.stop_recording_event.clear()
        app.bouton_enregistrer.configure(state="disabled")
        app.bouton_arreter.configure(state="normal")
        app.status.set("Enregistrement en cours...")

        def travail():
            chunks = []

            def record_chunk(indata, frames, time, status):
                if status:
                    app.root.after(0, lambda: app.status.set(str(status)))
                chunks.append(indata.copy())

            try:
                stream = sd.InputStream(
                    samplerate=enregistrer.SAMPLE_RATE,
                    channels=enregistrer.CHANNELS,
                    dtype="int16",
                    callback=record_chunk,
                )
                stream.start()
                app.stop_recording_event.wait(enregistrer.DURATION)
                stream.stop()
                stream.close()

                if not chunks:
                    app.root.after(
                        0,
                        lambda: (
                            app.status.set("Aucun son enregistre"),
                            messagebox.showwarning(
                                "Enregistrement", "Aucun son n'a ete capture."
                            ),
                        ),
                    )
                    return

                audio_data = np.concatenate(chunks, axis=0)
                audio_data = audio_data[: int(enregistrer.DURATION * enregistrer.SAMPLE_RATE)]
                os.makedirs(DOSSIER_MESSAGES, exist_ok=True)
                with wave.open(FICHIER_ENREGISTREMENT, "wb") as wf:
                    wf.setnchannels(enregistrer.CHANNELS)
                    wf.setsampwidth(2)
                    wf.setframerate(enregistrer.SAMPLE_RATE)
                    wf.writeframes(audio_data.tobytes())

                nettoye = nettoyer.nettoyer(FICHIER_ENREGISTREMENT)
                app.root.after(
                    0,
                    lambda: (
                        app.status.set(
                            "Enregistrement termine"
                            if nettoye
                            else "Enregistrement sauvegarde sans nettoyage"
                        ),
                        app.bouton_enregistrer.configure(state="normal"),
                        app.bouton_arreter.configure(state="disabled"),
                    ),
                )
            except Exception as erreur:
                app.root.after(
                    0,
                    lambda erreur=erreur: (
                        app.status.set("Erreur"),
                        app.bouton_enregistrer.configure(state="normal"),
                        app.bouton_arreter.configure(state="disabled"),
                        messagebox.showerror("Erreur", str(erreur)),
                    ),
                )

        app.recording_thread = threading.Thread(target=travail, daemon=True)
        app.recording_thread.start()

    def arreter_enregistrement(app):
        app.stop_recording_event.set()
        app.status.set("Arret de l'enregistrement...")
        app.bouton_arreter.configure(state="disabled")


def main():
    root = tk.Tk()
    SignauxGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

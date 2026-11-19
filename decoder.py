"""Décode un .wav encodé en M-FSK (voir encoder.py) et renvoie le texte.

Pour chaque lettre i (début à t = i * (DUREE_LETTRE + ESPACEMENT)) :
  1. on découpe la lettre en ceil(8 / k) tonalités de même durée
  2. pour chaque tonalité : FFT, fréquence dominante
  3. fréquence théorique la plus proche dans linspace(FMIN, FMAX, valence) -> indice
  4. indice écrit en binaire sur k bits ; on concatène, on garde 8 bits -> un caractère
"""
import math

import numpy as np
from scipy.io import wavfile

# valeurs fixe
FMIN = 500.0
FMAX = 8000.0
DUREE_LETTRE = 0.5
ESPACEMENT = 0.5


def frequence_dominante(segment, fs):
    """Fréquence du pic du spectre (fenêtre de Hann + zero-padding pour affiner)."""
    segment = segment * np.hanning(len(segment))
    n_fft = 1 << max(16, int(math.ceil(math.log2(len(segment)))))
    spectre = np.abs(np.fft.rfft(segment, n=n_fft))
    return np.argmax(spectre) * fs / n_fft


def decoder_wav(fichier, valence):
    k = int(round(math.log2(valence)))
    if valence < 2 or 2 ** k != valence:
        raise ValueError("La valence doit être une puissance de 2 (2, 4, 8, 16, 32)")

    fs, data = wavfile.read(fichier)
    if data.ndim > 1:  # stéréo -> mono
        data = data.mean(axis=1)
    data = data.astype(np.float64)

    frequences = np.linspace(FMIN, FMAX, valence)
    nb_lettre = int(round(DUREE_LETTRE * fs))  # échantillons par lettre
    pas = int(round((DUREE_LETTRE + ESPACEMENT) * fs))  # début d'une lettre -> début de la suivante
    nb_symboles = math.ceil(8 / k)
    nb_symbole = nb_lettre // nb_symboles  # échantillons par tonalité
    marge = int(0.2 * nb_symbole)  # on ignore les bords (fondus, transitions)

    nb_lettres = int(round((len(data) / fs + ESPACEMENT) / (DUREE_LETTRE + ESPACEMENT)))
    texte = ""
    for i in range(nb_lettres):
        bits = ""
        for j in range(nb_symboles):
            debut = i * pas + j * nb_symbole
            segment = data[debut + marge: debut + nb_symbole - marge]
            f = frequence_dominante(segment, fs)
            indice = int(np.argmin(np.abs(frequences - f)))
            bits += f"{indice:0{k}b}"
        texte += chr(int(bits[:8], 2))  # bits[:8] retire le remplissage de 0 (valence 8 ou 32)
    return texte
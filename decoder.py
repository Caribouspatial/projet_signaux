#!/usr/bin/env python3

import argparse
import math
import numpy as np
from scipy.io import wavfile

# valeurs fixe
FMIN = 500.0
FMAX = 8000.0
TS = 0.06  # durée d'UN symbole : doit être identique à Ts de encoder.py
ESPACEMENT = 0.5

FICHIER_DEFAUT = "messages/message.wav"
VALENCE_DEFAUT = 4  # doit être la valence utilisée à l'encodage

parser = argparse.ArgumentParser()
parser.add_argument("--fichier", default=FICHIER_DEFAUT)
parser.add_argument("--valence", type=int, default=VALENCE_DEFAUT)
args, _ = parser.parse_known_args()  # ignore les arguments ajoutés par Jupyter


def frequence_dominante(segment, fs):
    """Fréquence du pic du spectre (fenêtre de Hann + zero-padding pour affiner)."""
    segment = segment * np.hanning(len(segment))
    n_fft = 1 << max(16, int(math.ceil(math.log2(len(segment)))))
    spectre = np.abs(np.fft.rfft(segment, n=n_fft))
    return np.argmax(spectre) * fs / n_fft


def decoder(fichier, valence):
    k = int(round(math.log2(valence)))
    if valence < 2 or 2 ** k != valence:
        raise ValueError("La valence doit être une puissance de 2 (2, 4, 8, 16, 32)")

    fs, data = wavfile.read(fichier)
    if data.ndim > 1:  # stéréo -> mono
        data = data.mean(axis=1)
    data = data.astype(np.float64)

    frequences = np.linspace(FMIN, FMAX, valence)
    nb_symboles = math.ceil(8 / k)
    nb_symbole = int(round(TS * fs))  # échantillons par tonalité (même calcul que l'encodeur)
    nb_lettre = nb_symboles * nb_symbole  # échantillons par lettre (dépend maintenant de la valence)
    pas = nb_lettre + int(round(ESPACEMENT * fs))  # début d'une lettre -> début de la suivante
    marge = int(0.2 * nb_symbole)  # on ignore les bords (fondus, transitions)

    nb_lettres = int(round((len(data) + int(round(ESPACEMENT * fs))) / pas))
    texte = ""
    for i in range(nb_lettres):
        bits = ""
        for j in range(nb_symboles):
            debut = i * pas + j * nb_symbole
            segment = data[debut + marge: debut + nb_symbole - marge]
            f = frequence_dominante(segment, fs)
            indice = int(np.argmin(np.abs(frequences - f)))  # fréquence théorique la plus proche
            bits += f"{indice:0{k}b}"
        bits = bits[:8]  # retire le remplissage de 0 (valence 8 ou 32)
        texte += chr(int(bits, 2))
    return texte


if __name__ == "__main__":
    print(decoder(args.fichier, args.valence))
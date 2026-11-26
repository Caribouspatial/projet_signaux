#!/usr/bin/env python3

import argparse
import math
import numpy as np
from scipy.io import wavfile
"""Décode un message.wav encodé en M-FSK (voir l'encodeur) et affiche le texte.

Principe, pour chaque lettre i (début à t = i * (ceil(8 / k) * TS + ESPACEMENT)) :
  1. on découpe la lettre en ceil(8 / k) tonalités de durée TS chacune
  2. pour chaque tonalité, on fait une FFT et on prend la fréquence dominante
  3. on cherche la fréquence la plus proche dans linspace(FMIN, FMAX, valence) -> son indice
  4. l'indice est écrit en binaire sur k bits ; on concatène, on garde 8 bits -> un caractère

Usage :
    python decoder.py --valence 4
    python decoder.py --fichier autre.wav --valence 16
Sous Jupyter/IPython : modifier FICHIER_DEFAUT et VALENCE_DEFAUT ci-dessous.
"""

# valeurs fixe
FMIN = 500.0
FMAX = 8000.0
TS = 0.06  # durée d'UN symbole : doit être identique à Ts de encoder.py
ESPACEMENT = 0.5

FICHIER_DEFAUT = "messages/message.wav"
VALENCE_DEFAUT = 4  # doit être la valence utilisée à l'encodage
FREQUENCE_MARQUEUR_DEBUT = 300.0
FREQUENCE_MARQUEUR_FIN = 400.0
NB_SYMBOLES_MARQUEUR = 3

parser = argparse.ArgumentParser()
parser.add_argument("--fichier", default=FICHIER_DEFAUT)
parser.add_argument("--valence", type=int, default=VALENCE_DEFAUT)
args, _ = parser.parse_known_args()  # ignore les arguments ajoutés par Jupyter


def frequence_dominante(segment, fs):
    """Fréquence du pic du spectre (fenêtre de Hann + zero-padding pour affiner)."""
    if len(segment) == 0:
        raise ValueError("Segment audio vide : le fichier est incomplet ou la valence est incorrecte.")
    segment = segment * np.hanning(len(segment))
    n_fft = 1 << max(16, int(math.ceil(math.log2(len(segment)))))
    spectre = np.abs(np.fft.rfft(segment, n=n_fft))
    return np.argmax(spectre) * fs / n_fft


def trouver_marqueur(data, fs, frequence):
    """Repère une tonalité de marqueur répétée dans un enregistrement."""
    nb_symbole = int(round(TS * fs))
    pas_recherche = max(1, int(round(0.01 * fs)))
    seuil = np.max(np.abs(data)) * 0.001
    correspondances = []

    for debut in range(0, len(data) - nb_symbole + 1, pas_recherche):
        segment = data[debut:debut + nb_symbole]
        if np.sqrt(np.mean(segment ** 2)) <= seuil:
            continue
        fenetre = segment * np.hanning(len(segment))
        spectre = np.abs(np.fft.rfft(fenetre, n=8192))
        pic = np.argmax(spectre) * fs / 8192
        if abs(pic - frequence) <= 80:
            correspondances.append(debut)

    if not correspondances:
        return None

    debut_groupe = precedent = correspondances[0]
    duree_min = (NB_SYMBOLES_MARQUEUR - 1) * TS - 0.03
    for position in correspondances[1:]:
        if position - precedent > 2 * pas_recherche:
            if precedent - debut_groupe >= duree_min * fs:
                if debut_groupe == 0:
                    return 0
                return debut_groupe + nb_symbole - pas_recherche
            debut_groupe = position
        precedent = position

    if precedent - debut_groupe >= duree_min * fs:
        if debut_groupe == 0:
            return 0
        return debut_groupe + nb_symbole - pas_recherche
    return None


def decoder_lettres(data, fs, frequences, k, debut, nombre):
    nb_symboles = math.ceil(8 / k)
    nb_symbole = int(round(TS * fs))
    nb_lettre = nb_symboles * nb_symbole
    pas = nb_lettre + int(round(ESPACEMENT * fs))
    marge = int(0.2 * nb_symbole)
    texte = ""

    for i in range(nombre):
        bits = ""
        for j in range(nb_symboles):
            position = debut + i * pas + j * nb_symbole
            segment = data[position + marge:position + nb_symbole - marge]
            if len(segment) == 0:
                raise ValueError(
                    "Enregistrement incomplet ou valence incorrecte : "
                    "aucune tonalité complète à cette position."
                )
            f = frequence_dominante(segment, fs)
            indice = int(np.argmin(np.abs(frequences - f)))
            bits += f"{indice:0{k}b}"
        texte += chr(int(bits[:8], 2))
    return texte


def decoder(fichier, valence):
    if not isinstance(valence, (int, np.integer)) or valence < 2 or valence & (valence - 1):
        raise ValueError("La valence doit être une puissance de 2 (2, 4, 8, 16, 32)")
    valence = int(valence)
    k = valence.bit_length() - 1

    fs, data = wavfile.read(fichier)
    if data.ndim > 1:  # stéréo -> mono
        data = data.mean(axis=1)
    if data.size == 0:
        raise ValueError("Le fichier WAV est vide.")
    if np.issubdtype(data.dtype, np.integer) and np.max(
        np.abs(data.astype(np.float64))
    ) <= 2:
        raise ValueError(
            "Aucun signal audio détectable dans l'enregistrement. "
            "Vérifiez la source audio puis réenregistrez le message."
        )
    data = data.astype(np.float64)

    frequences = np.linspace(FMIN, FMAX, valence)
    nb_symboles = math.ceil(8 / k)
    nb_symbole = int(round(TS * fs))  # échantillons par tonalité (même calcul que l'encodeur)
    nb_lettre = nb_symboles * nb_symbole  # échantillons par lettre (dépend maintenant de la valence)
    pas = nb_lettre + int(round(ESPACEMENT * fs))  # début d'une lettre -> début de la suivante

    debut_marqueur = trouver_marqueur(data, fs, FREQUENCE_MARQUEUR_DEBUT)
    fin_marqueur = trouver_marqueur(data, fs, FREQUENCE_MARQUEUR_FIN)
    if debut_marqueur is not None or fin_marqueur is not None:
        if debut_marqueur is None or fin_marqueur is None:
            raise ValueError("Marqueur de début ou de fin manquant : message incomplet.")
        debut_donnees = (
            debut_marqueur
            + NB_SYMBOLES_MARQUEUR * nb_symbole
            + int(round(ESPACEMENT * fs))
        )
        nombre_lettres = int(round((fin_marqueur - debut_donnees) / pas))
        if nombre_lettres < 1:
            raise ValueError("Aucune donnée trouvée entre les marqueurs.")
        return decoder_lettres(data, fs, frequences, k, debut_donnees, nombre_lettres)

    # Compatibilité avec les anciens fichiers WAV sans marqueurs.
    if len(data) < nb_lettre:
        raise ValueError("Le fichier ne contient pas une lettre complète.")
    debut_rms = np.sqrt(np.mean(data[:nb_symbole] ** 2))
    if debut_rms <= np.max(np.abs(data)) * 0.01:
        raise ValueError(
            "Marqueurs de synchronisation absents et silence au début du fichier. "
            "Réencodez puis réenregistrez le message avec la version actuelle."
        )
    nb_lettres = (len(data) - nb_lettre) // pas + 1
    return decoder_lettres(data, fs, frequences, k, 0, nb_lettres)


if __name__ == "__main__":
    print(decoder(args.fichier, args.valence))
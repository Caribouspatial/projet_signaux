"""
nettoyer.py : nettoie un enregistrement micro pour que decoder.py puisse le lire.

nettoyer(fichier) remplace le fichier par sa version nettoyée.
Si aucun son n'est détecté, le fichier n'est PAS touché (rien n'est écrit, rien n'est copié)
et la fonction renvoie False.

Étapes (le signal n'est modifié que légèrement) :
  1. stéréo -> mono, suppression de la composante continue
  2. filtre passe-bande autour des fréquences utiles (FMIN..FMAX), sans déphasage
  3. détection de l'activité (enveloppe) et mise à zéro des silences (bruit, échos)
  4. recalage : le début du 1er son est placé à t = 0 (le décodeur suppose que le message
     commence à 0 s), la fin est coupée juste après le dernier son
  5. normalisation de l'amplitude
"""
import os

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt, hilbert, medfilt

# mêmes valeurs que decoder.py
FMIN = 500.0
FMAX = 8000.0

RAPPORT_MIN = 10.0   # niveau des sons / niveau du bruit de fond, minimum pour accepter
CRETE_MIN = 100.0    # niveau absolu minimal des sons (échelle int16)


def _ms(x, fs):
    return int(round(x * fs / 1000))


def _lisser(x, n):
    """Moyenne glissante de n échantillons."""
    return np.convolve(x, np.ones(n) / n, mode="same")


def _traiter(data, fs, decalage_ms=0.0):
    """Renvoie le signal nettoyé (int16) ou None si aucun son n'est détecté."""
    data = data.astype(np.float64)
    if data.ndim > 1:  # stéréo -> mono
        data = data.mean(axis=1)
    if len(data) < _ms(300, fs):
        return None
    data = data - data.mean()

    # 1) passe-bande (zéro déphasage : ne décale pas les débuts de sons)
    haut = min(FMAX * 1.15, fs / 2 * 0.95)
    sos = butter(6, [FMIN * 0.7, haut], btype="bandpass", fs=fs, output="sos")
    filtre = sosfiltfilt(sos, data)

    # 2) enveloppe et seuil
    env = _lisser(np.abs(hilbert(filtre)), _ms(5, fs))
    plancher = np.percentile(env, 20)   # bruit de fond
    crete = np.percentile(env, 99)      # niveau des sons
    if crete < CRETE_MIN or crete < RAPPORT_MIN * max(plancher, 1e-9):
        return None
    actif = env > plancher + 0.12 * (crete - plancher)

    # ignore les bruits brefs, comble les petits trous (< 80 ms) dans une lettre
    actif = medfilt(actif.astype(np.uint8), _ms(80, fs) | 1).astype(bool)
    idx = np.flatnonzero(actif)
    if len(idx) == 0:
        return None
    coupures = np.flatnonzero(np.diff(idx) > _ms(100, fs))
    debuts = np.r_[idx[0], idx[coupures + 1]]
    fins = np.r_[idx[coupures], idx[-1]]
    longs = (fins - debuts) > _ms(100, fs)
    debuts, fins = debuts[longs], fins[longs]
    if len(debuts) == 0:
        return None

    # 3) début précis du 1er son : passage à 50 % du palier
    d0 = debuts[0]
    palier = np.median(env[d0 + _ms(15, fs): d0 + _ms(45, fs)])
    depart = max(0, d0 - _ms(40, fs))
    zone = env[depart: d0 + _ms(60, fs)]
    t0 = depart + int(np.argmax(zone > 0.5 * palier)) + _ms(decalage_ms, fs)
    t0 = max(0, t0)

    # fin précise du dernier son : dernier passage à 50 % du palier
    f1 = fins[-1]
    palier_f = np.median(env[max(0, f1 - _ms(150, fs)): max(1, f1 - _ms(70, fs))])
    debut_z = max(0, f1 - _ms(70, fs))
    zone = env[debut_z: f1 + _ms(40, fs)]
    t1 = debut_z + int(len(zone) - 1 - np.argmax((zone > 0.5 * palier_f)[::-1]))
    t1 = min(len(filtre), t1 + _ms(100, fs))  # marge : le dernier son (500 Hz) est faible

    # 4) mise à zéro des silences (fondu de 5 ms) puis recalage
    masque = np.zeros(len(filtre))
    for a, b in zip(debuts, fins):
        masque[max(0, a - _ms(25, fs)): b + _ms(120, fs)] = 1.0
    masque = _lisser(masque, _ms(5, fs))
    propre = (filtre * masque)[t0:t1]
    if len(propre) == 0 or np.max(np.abs(propre)) == 0:
        return None

    # 5) normalisation (crête à 90 % du maximum int16)
    propre = propre * (0.9 * 32767 / np.max(np.abs(propre)))
    return propre.astype(np.int16), len(debuts), t0 / fs, t1 / fs


def nettoyer(fichier, decalage_ms=0.0):
    """Nettoie `fichier` sur place. Renvoie True si modifié, False si aucun son (fichier intact)."""
    fs, data = wavfile.read(fichier)
    resultat = _traiter(data, fs, decalage_ms)
    if resultat is None:
        print("Aucun son détecté : enregistrement non modifié.")
        return False

    propre, nb_lettres, t0, t1 = resultat
    # écriture dans un fichier temporaire puis remplacement : jamais de fichier à moitié écrit
    temporaire = fichier + ".tmp.wav"
    try:
        wavfile.write(temporaire, fs, propre)
        os.replace(temporaire, fichier)
    finally:
        if os.path.exists(temporaire):
            os.remove(temporaire)
    print(f"Enregistrement nettoyé : {nb_lettres} lettres, son de {t0:.2f} s à {t1:.2f} s "
          f"-> durée {len(propre) / fs:.2f} s")
    return True


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Nettoie un .wav sur place (intact si aucun son).")
    p.add_argument("fichier")
    p.add_argument("--decalage", type=float, default=0.0, help="correction manuelle du début, en ms")
    a = p.parse_args()
    nettoyer(a.fichier, a.decalage)
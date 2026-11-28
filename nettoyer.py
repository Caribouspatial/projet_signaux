import os
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d, minimum_filter1d, uniform_filter1d
from scipy.signal import butter, sosfiltfilt, hilbert

# valeurs fixe
FMIN = 500.0
FMAX = 8000.0
ESPACEMENT = 0.5      # silence entre deux lettres (s), identique à l'encodeur
CRETE_MIN = 100.0     # niveau absolu minimal des sons (échelle int16)
TONALITE_MIN = 20.0   # pic du spectre / moyenne du spectre : bruit ~ 6-10, son pur >> 20


def _ms(x, fs):
    return int(round(x * fs / 1000))

#Moyenne glissante de n échantillons (temps linéaire, même pour de longs enregistrements)
def _lisser(x, n):
    return uniform_filter1d(np.asarray(x, dtype=np.float64), size=max(1, n), mode="nearest")

#Tonalité et fréquence du pic pour chaque trame (trame i = échantillons [i*hop, i*hop+win])
def _spectres(filtre, fs, win, hop):
    trames = sliding_window_view(filtre, win)[::hop]
    f = np.fft.rfftfreq(win, 1 / fs)
    bande = (f >= FMIN * 0.8) & (f <= min(FMAX * 1.15, fs / 2 * 0.95))
    tonalite = np.empty(len(trames))
    pic = np.empty(len(trames))
    fenetre = np.hanning(win)
    for a in range(0, len(trames), 2000):            # par blocs : mémoire limitée
        P = np.abs(np.fft.rfft(trames[a:a + 2000] * fenetre, axis=1)[:, bande]) ** 2
        tonalite[a:a + 2000] = P.max(axis=1) / (P.mean(axis=1) + 1e-12)
        pic[a:a + 2000] = f[bande][P.argmax(axis=1)]
    return tonalite, pic

# Renvoie (signal int16, nb lettres, début s, fin s, complété s) ou None si aucun son
def _traiter(data, fs, decalage_ms=0.0):

    data = data.astype(np.float64)
    if data.ndim > 1:  # stéréo -> mono
        data = data.mean(axis=1)
    if len(data) < _ms(300, fs):
        return None
    data = data - data.mean()

    # passe-bande (zéro déphasage : ne décale pas les débuts de sons)
    haut = min(FMAX * 1.15, fs / 2 * 0.95)
    sos = butter(6, [FMIN * 0.7, haut], btype="bandpass", fs=fs, output="sos")
    filtre = sosfiltfilt(sos, data)
    env = _lisser(np.abs(hilbert(filtre)), _ms(5, fs))
    if np.percentile(env, 99) < CRETE_MIN:
        return None

    # trames tonales
    win = 1 << int(round(np.log2(0.023 * fs)))   # ~ 23 ms
    hop = _ms(5, fs)
    if len(filtre) < win + hop:
        return None
    tonalite, pic = _spectres(filtre, fs, win, hop)
    # trame "tonale" = spectre pointu ET même fréquence de pic sur ~35 ms (un vrai son garde sa
    # fréquence ; les bruits de la pièce, eux, font varier le pic)
    voisins = 7
    stable = (maximum_filter1d(pic, voisins) - minimum_filter1d(pic, voisins)) <= 100
    tonal = (tonalite > TONALITE_MIN) & stable

    # comble les trous de moins de 40 ms (changements de fréquence) sans décaler les bords
    g = max(1, _ms(40, fs) // hop)
    dilate = uniform_filter1d(tonal.astype(float), size=g, mode="nearest") > 0
    actif = uniform_filter1d(dilate.astype(float), size=g, mode="nearest") > 0.999
    a = np.r_[False, actif, False].astype(np.int8)
    d = np.diff(a)
    trames_debut = np.flatnonzero(d == 1)
    trames_fin = np.flatnonzero(d == -1) - 1
    long = (trames_fin - trames_debut + 1) >= _ms(100, fs) // hop   # au moins 100 ms
    trames_debut, trames_fin = trames_debut[long], trames_fin[long]
    if len(trames_debut) == 0:
        return None

    # une lettre dure à peu près pareil : on écarte les segments bien plus courts (clic de touche),
    # sauf s'ils touchent la fin de l'enregistrement (lettre coupée par l'arrêt)
    durees = (trames_fin - trames_debut) * hop + win
    ref = np.median(durees) if len(durees) >= 3 else durees.max()
    touche_fin = trames_fin * hop + win >= len(filtre) - _ms(150, fs)
    garde = (durees >= 0.7 * ref) | touche_fin
    trames_debut, trames_fin = trames_debut[garde], trames_fin[garde]
    if len(trames_debut) == 0:
        return None

    # début précis de chaque lettre : filtre étroit autour de la fréquence de son 1er son
    def debut_precis(s):
        cs = s * hop
        i = min(s + win // hop + 2, len(pic) - 1)       # trame entièrement dans le 1er symbole
        f0 = pic[i]
        etroit = butter(4, [max(50.0, f0 - 150), min(fs / 2 * 0.95, f0 + 150)],
                        btype="bandpass", fs=fs, output="sos")
        a0 = max(0, cs - _ms(60, fs))
        b0 = min(len(filtre), cs + _ms(120, fs))
        e = _lisser(np.abs(hilbert(sosfiltfilt(etroit, filtre[a0:b0]))), _ms(2, fs))
        p0, p1 = cs + win + _ms(5, fs) - a0, cs + _ms(50, fs) - a0
        palier = np.median(e[p0:p1]) if p1 > p0 else e.max()
        z0, z1 = max(0, cs - _ms(25, fs) - a0), cs + win + _ms(5, fs) - a0
        return a0 + z0 + int(np.argmax(e[z0:z1] > 0.5 * palier))

    debuts = np.array([debut_precis(s) for s in trames_debut])
    fins = trames_fin * hop + win

    # pas entre lettres (début -> début) = durée d'une lettre + ESPACEMENT
    pas = None
    if len(debuts) >= 2:
        ecarts = np.diff(debuts) / fs
        pas = float(np.median(ecarts[ecarts < 1.3 * ecarts.min()]))
        if pas <= ESPACEMENT + 0.05:   # lettre de moins de 50 ms : estimation absurde
            pas = None

    if pas is not None:
        duree_lettre = int(round((pas - ESPACEMENT) * fs))
        # lettre suivante attendue : on la garde si la zone est tonale presque en continu
        while True:
            e = int(debuts[-1] + pas * fs)
            if e + duree_lettre // 2 > len(filtre):
                break
            i0 = -(-(e + _ms(10, fs)) // hop)
            i1 = (min(e + duree_lettre, len(filtre)) - win) // hop
            if i1 - i0 >= 6 and np.mean(actif[i0:i1 + 1]) > 0.8:
                debuts = np.r_[debuts, e]
            else:
                break
        t1 = int(debuts[-1] + duree_lettre + _ms(50, fs))   # fin = début dernière lettre + sa durée
        fenetres = [(d0 - _ms(25, fs), d0 + duree_lettre + _ms(60, fs)) for d0 in debuts]
    else:                                                   # une seule lettre : pas de pas mesurable
        t1 = int(fins[-1] + _ms(150, fs))
        fenetres = [(d0 - _ms(25, fs), f0 + _ms(120, fs)) for d0, f0 in zip(debuts, fins)]

    # enregistrement arrêté trop tôt : on complète par du silence pour que le décodeur ait
    # toute la dernière lettre (sinon il plante ou la perd)
    complete = max(0, t1 - len(filtre))
    if complete:
        filtre = np.r_[filtre, np.zeros(complete)]
        env = np.r_[env, np.zeros(complete)]

    # gain par lettre (même volume pour toutes) ; silences à zéro, fondus de 5 ms
    gain = np.zeros(len(filtre))
    for a0, b0 in fenetres:
        a0, b0 = max(0, a0), min(len(filtre), b0)
        niveau = np.percentile(env[a0:b0], 99)
        if niveau > 0:
            gain[a0:b0] = 1.0 / niveau
    gain = _lisser(gain, _ms(5, fs))

    t0 = max(0, int(debuts[0]) + _ms(decalage_ms, fs))
    propre = (filtre * gain)[t0:t1]
    if len(propre) == 0 or np.max(np.abs(propre)) == 0:
        return None

    # normalisation (crête à 90 % du maximum int16)
    propre = propre * (0.9 * 32767 / np.max(np.abs(propre)))
    return propre.astype(np.int16), len(debuts), t0 / fs, t1 / fs, complete / fs

# Nettoie `fichier` sur place. Renvoie True si modifié, False si aucun son (fichier intact)
def nettoyer(fichier, decalage_ms=0.0):
    fs, data = wavfile.read(fichier)
    resultat = _traiter(data, fs, decalage_ms)
    if resultat is None:
        print("Aucun son détecté : enregistrement non modifié.")
        return False

    propre, nb_lettres, t0, t1, complete = resultat
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
    if complete > 0.02:
        print(f"Attention : l'enregistrement s'est arrêté {complete:.2f} s trop tôt, la fin de la "
              f"dernière lettre manque. Appuyer sur Entrée un peu après la fin du son.")
    return True
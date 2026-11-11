import os
import math
import wave #pour écrire les fichiers .wav
import numpy as np #calculs
import matplotlib.pyplot as plt # débug


# valeurs fixe
Fmin = 500 # Hz
Fmax = 8000 # Hz
espacement = 0.5 # seconde : silence entre deux lettres
duree_lettre = 0.5 # seconde : durée des tonalités d'une lettre
fs = 44100 # Hz : fréquence d'échantillonnage du .wav (doit être > 2 x Fmax)
amplitude = 0.8 # volume (0 à 1)
rampe = 0.005 # seconde : fondu au début et à la fin de chaque tonalité (évite les clics)

"""
Structure du .wav (pour le décodage) :

La lettre numéro i (la première = 0) commence à t = i * (duree_lettre + espacement) secondes
Elle contient (8 / k) tonalités de même durée, une par groupe de k bits (de gauche à droite)
La fréquence d'une tonalité = frequences[valeur du groupe], avec frequences = linspace(Fmin, Fmax, valence)
Si 8 n'est pas un multiple de k (valence 8 ou 32), le dernier groupe est complété par des 0 à droite
Entre deux lettres : silence de durée "espacement" (pas de silence après la dernière lettre)
"""

###### Fonctions
# fonction qui demande d'écrire le texte que l'on veut, puis de choisir une valence
def demandeTexte():
    k = 0
    texte = input("Veuillez entrer le texte à encoder : ")
    if len(texte) == 0:
        print("Le texte est vide. Veuillez réessayer.")
        return demandeTexte()
    if len(texte) > 128:
        print("Le texte est trop long. Veuillez entrer un texte de 256 caractères maximum.")
        return demandeTexte()
    if any(ord(c) > 255 for c in texte):
        print("Le texte contient un caractère qui ne tient pas sur 8 bits (par exemple €). Veuillez réessayer.")
        return demandeTexte()
    try:
        valence = int(input("Veuillez entrer la valence (puissance de 2 : 2, 4, 8, 16, 32) : "))
    except ValueError:
        print("La valence doit être un nombre entier. Veuillez réessayer.")
        return demandeTexte()
    if valence < 2:
        print("La valence doit être supérieure ou égale à 2. Veuillez réessayer.")
        return demandeTexte()
    if valence > 32:
        print("La valence est trop grande. Veuillez entrer une valence de 32 ou moins.")
        return demandeTexte()
    try:
        k = bits_par_symbole(valence)
    except ValueError as erreur:
        print(erreur)
        return demandeTexte()
    return texte, valence, k

# fonction de vérification valence (puissance de 2)

def bits_par_symbole(valence):
    k = int(round(math.log2(valence))) if valence >= 2 else 0
    if valence < 2 or 2 ** k != valence:
        raise ValueError("La valence doit être une puissance de 2 (2, 4, 8, 16, 32...)")
    return k

# fonction de transformation en code ascii binaire, du texte

def transformationascii(t):
    arrayascii = []
    for c in t:
        arrayascii.append(f"{ord(c):08b}")
    return arrayascii

# fonction qui coupe les 8 bits d'une lettre en groupes de k bits
# ex : '01000001' avec k = 2 -> [1, 0, 0, 1] (chaque valeur est comprise entre 0 et 1)

def decoupage_symboles(mot, k):
    nb_symboles = math.ceil(len(mot) / k)
    mot = mot.ljust(nb_symboles * k, "0") # complète par des 0 à droite si 8 n'est pas multiple de k
    return [int(mot[i * k:(i + 1) * k], 2) for i in range(nb_symboles)]

# fonction de création de l'array du texte du code ascii vers le binaire en fonction de la valence
"""
En entrée : la liste de mots de 8 bits (transformationascii), la valence et k = log2(valence)
En sortie : array numpy (float32, entre -1 et 1) = les échantillons audio, prêts pour le .wav
"""

def creation_array(arrayascii, valence, k):
    if Fmax >= fs / 2:
        raise ValueError(f"Fmax doit être inférieure à fs/2 = {fs / 2:.0f} Hz")
    frequences = np.linspace(Fmin, Fmax, valence) # une fréquence par valeur possible d'un groupe de bits
    nb_lettre = int(round(duree_lettre * fs)) # échantillons occupés par une lettre
    silence = np.zeros(int(round(espacement * fs)))

    lettres = []
    for mot in arrayascii:
        if len(mot) != 8:
            raise ValueError(f"le mot {mot} ne fait pas 8 bits")

        symboles = decoupage_symboles(mot, k)
        nb_symbole = nb_lettre // len(symboles) # échantillonage
        t = np.arange(nb_symbole) / fs
        enveloppe = np.ones(nb_symbole) # fondu d'entrée et de sortie : évite les clics de transistions
        r = min(int(rampe * fs), nb_symbole // 2)
        if r > 0:
            fondu = 0.5 * (1 - np.cos(np.pi * np.arange(r) / r))
            enveloppe[:r] = fondu
            enveloppe[-r:] = fondu[::-1]

        lettre = np.concatenate([np.sin(2 * np.pi * frequences[s] * t) * enveloppe for s in symboles])
        lettre = np.pad(lettre, (0, nb_lettre - len(lettre))) # durée exacte : chaque lettre a la même longueur
        lettres.append(lettre)

    morceaux = [] # lettre, silence, lettre, silence, ..., lettre
    for i, lettre in enumerate(lettres):
        if i > 0:
            morceaux.append(silence)
        morceaux.append(lettre)
    return (amplitude * np.concatenate(morceaux)).astype(np.float32)

# fonction de transformation de array en .wav, utiliser bibliothèque wave
# ATT remplacer le chemin par celui correspondant sur votre PC
def array_vers_wav(array, nom_fichier="message.wav"):
    chemin = os.path.join('/Users/user/Desktop/BLOC3/SignauxIII/m-fsk/messages', nom_fichier) # le dossier /messages existe déjà
    pcm = (np.clip(array, -1, 1) * 32767).astype("<i2") # float -> entiers 16 bits
    with wave.open(chemin, "wb") as fichier:
        fichier.setnchannels(1) # mono
        fichier.setsampwidth(2) # 2 octets = 16 bits
        fichier.setframerate(fs)
        fichier.writeframes(pcm.tobytes())
    return chemin
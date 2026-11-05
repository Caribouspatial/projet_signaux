import argparse
import binascii # redondance
import math
import sys
import wave #pour écrire les fichiers .wav

import numpy as np #calculs
import matplotlib.pyplot as plt # débug

#python encoder.py encoder "texte" --m 4 -> ligne de code pour lancer encoder.py

# valeurs fixe
Fmin = 500 # Hz
Fmax = 8000 # Hz
espacement = 0.5 # seconde
duree_lettre = 0.5 # seconde
valence = 4



t = "test0123"

###### Fonctions

# fonction qui demande d'écrire le texte que l'on veut, puis de choisir une valence

def demandeTexte():
    k = 0
    texte = input("Veuillez entrer le texte à encoder : ")
    valence = int(input("Veuillez entrer la valence (multiple de 2) : "))
    if valence < 2:
        print("La valence doit être supérieure ou égale à 2. Veuillez réessayer.")
        return demandeTexte()
    if len(texte) > 256:
        print("Le texte est trop long. Veuillez entrer un texte de moins de 256 caractères.")
        return demandeTexte()
    if valence > 32:
        print("La valence est trop grande. Veuillez entrer une valence de 32 ou moins.")
        return demandeTexte()
    try:
        k = bits_par_symbole(valence)
    except ValueError as e:
        print(e)
        return demandeTexte()
    return texte, valence, k

# fonction de vérification valence (multiple de 2)

def bits_par_symbole(valence):
    k = int(round(math.log2(valence))) if valence >= 2 else 0
    if valence < 2 or 2 ** k != valence:
        raise ValueError("La valence doit être une puissance de 2 (2, 4, 8, 16, 32...)")
    return k 

# fonction de transformation en binaire (selon standard ascii), du texte
def transformationascii(t):
    arrayascii = []
    for c in t:
        arrayascii.append(f"{ord(c):08b}")
    return arrayascii

# fonction de création de l'array du texte en binaire en fonction de la valence
# fonction de transformation de l'array en .wav, utiliser bibliothèque wave


# fonction pour jouer le .wav

# test a enlever
transformationascii(t)


#toutefin/optionnel
#fonction changement du texte en lowercase et é,è,E -> e

texte, valence, k = demandeTexte()
texte_binaire = transformationAscii(texte)
print("Texte en binaire : ", texte_binaire, valence, k)




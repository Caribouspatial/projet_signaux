import argparse
import binascii # redondance
import math
import sys
import wave #pour écrire les fichiers .wav

#import numpy as np #calculs
#import matplotlib.pyplot as plt # débug

#python encoder.py encoder "texte" --m 4 -> ligne de code pour lancer encoder.py

# valeurs fixe
Fmin = 500 # Hz
Fmax = 8000 # Hz
espacement = 0.5 # seconde
duree_lettre = 0.5 # seconde
valence = 4

t = "test0123"
######Fonction
# fonction qui demande d'écrire le texte que l'on veut, puis de choisir une valence

# fonction de vérification valence (multiple de 2)

# fonction de transformation en binaire (selon standard ascii), du texte
def transformationAscii(t):
    arrayAscii = []
    for c in t:
        arrayAscii.append(f"{ord(c):08b}")
    return arrayAscii


transformationAscii(t)
# fonction de création de l'array du texte en binaire en fonction de la valence
# fonction de transformation de l'array en .wav, utiliser bibliothèque wave


# fonction pour jouer le .wav

"""# fonction de code gray
def gray(i): # décalage de 1 avec XOR
    return i ^ (i >> 1)"""

#toutefin/optionnel
#fonction changement du texte en lowercase et é,è,E -> e



import os
import argparse
import binascii # redondance
import math
import sys
import wave #pour écrire les fichiers .wav

import numpy as np #calculs
import matplotlib.pyplot as plt # débug

#python decoder.py decoder --m 4 -> ligne de codde pour lancer decoder.py

# valeurs fixe
Fmin = 500 # Hz
Fmax = 8000 # Hz
espacement = 0.5 # seconde : silence entre deux lettres
duree_lettre = 0.5 # seconde : durée des tonalités d'une lettre
fs = 44000 # Hz : fréquence d'échantillonnage du .wav (doit être > 2 x Fmax)

# fonction d'analyse fréquentielle du .wav
#boucle qui ajoute chaque nouvelle lettre à la fin d'un string

# fonction d'affichage du message après avoir arrêté la fonction d'analyse

# fonction d'enregistrement (avoir un stop manuel) de l'audio en .wav
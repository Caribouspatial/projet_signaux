import argparse
import binascii # redondance
import math
import sys
import wave #pour écrire les fichiers .wav

import numpy as np #calculs
import matplotlib.pyplot as plt # débug

# valeurs fixe
Fmin = 500 #Hz
Fmax = 8000 #Hz
espacement = 0.5 # seconde
table_lettre = {
    " " : 500,
    "a" : 700,
    "b" : 900,
    "c" : 1100,
    "d" : 1300,
    "e" : 1500,
    "f" : 1700,
    "g" : 1900,
    "h" : 2100,
    "i" : 2300,
    "j" : 2500,
    "k" : 2700,
    "l" : 2900,
    "m" : 3100,
    "n" : 3300,
    "o" : 3500,
    "p" : 3700,
    "q" : 3900,
    "r" : 4100,
    "s" : 4300,
    "t" : 4500,
    "u" : 4700,
    "v" : 4900,
    "w" : 5100,
    "x" : 5300,
    "y" : 5500,
    "z" : 5700,
    "0" : 5900,
    "1" : 6100,
    "2" : 6300,
    "3" : 6500,
    "4" : 6700,
    "5" : 6900,
    "6" : 7100,
    "7" : 7300,
    "8" : 7500,
    "9" : 7700,
}
#python decoder.py decoder --m 4 -> ligne de codde pour lancer decoder.py

# fonction d'enregistrement (avoir un stop manuel) de l'audio en .wav

# fonction d'analyse fréquentielle du .wav
#boucle qui ajoute chaque nouvelle lettre à la fin d'un string

# fonction d'affichage du message après avoir arrêté la fonction d'analyse
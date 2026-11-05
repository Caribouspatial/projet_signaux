import argparse
import binascii # redondance
import math
import sys
import wave #pour écrire les fichiers .wav

import numpy as np #calculs
import matplotlib.pyplot as plt # débug

#python decoder.py decoder --m 4 -> ligne de codde pour lancer decoder.py

# valeurs fixe
Fmin = 500 #Hz
Fmax = 8000 #Hz
espacement = 0.5 # seconde


# fonction d'enregistrement (avoir un stop manuel) de l'audio en .wav

# fonction d'analyse fréquentielle du .wav
#boucle qui ajoute chaque nouvelle lettre à la fin d'un string

# fonction d'affichage du message après avoir arrêté la fonction d'analyse
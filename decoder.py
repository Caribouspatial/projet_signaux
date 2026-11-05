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
table_lettre_decodage = {
    500 : " ",
    700: "a",
    900: "b",
    1100: "c",
    1300: "d",
    1500: "e",
    1700: "f",
    1900: "g",
    2100: "h",
    2300: "i",
    2500: "j",
    2700: "k",
    2900: "l",
    3100: "m",
    3300: "n",
    3500: "o",
    3700: "p",
    3900: "q",
    4100: "r",
    4300: "s",
    4500: "t",
    4700: "u",
    4900: "v",
    5100: "w",
    5300: "x",
    5500: "y",
    5700: "z",
    5900: "0",
    6100: "1",
    6300: "2",
    6500: "3",
    6700: "4",
    6900: "5",
    7100: "6",
    7300: "7",
    7500: "8",
    7700: "9",
}
#python decoder.py decoder --m 4 -> ligne de codde pour lancer decoder.py

# fonction d'enregistrement (avoir un stop manuel) de l'audio en .wav

# fonction d'analyse fréquentielle du .wav
#boucle qui ajoute chaque nouvelle lettre à la fin d'un string

# fonction d'affichage du message après avoir arrêté la fonction d'analyse
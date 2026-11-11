import numpy as np

import encoder, decoder

Fmin = 500 # Hz
Fmax = 8000 # Hz
fs = 44000 # Hz : fréquence d'échantillonnage du .wav (doit être > 2 x Fmax)

#lanceur de code
choix = input('Taper "1"  pour encoder, "2" pour decoder et "3" pour jouer le dernier texte encoder: ')
if choix == "1":
    texte, valence, k = encoder.demandeTexte()
    texte_binaire = encoder.transformationascii(texte)
    array = encoder.creation_array(texte_binaire, valence, k)
    encoder.array_vers_wav(array, "message.wav")
    print("Texte en binaire : ", texte_binaire, valence, k)
    print("Fréquences (Hz) :", np.linspace(Fmin, Fmax, valence))
    print(f"message.wav écrit : {len(array)} échantillons, {len(array) / fs:.1f} s")
elif choix == "2":
    print("décoder")
elif choix == "3":
    print("jouer .wav")
else:
    print("Erreur taper 1, 2 ou 3")
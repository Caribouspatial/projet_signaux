import numpy as np
import encoder, decoder, jouer

Fmin = 500 # Hz
Fmax = 8000 # Hz
fs = 44000 # Hz : fréquence d'échantillonnage du .wav (doit être > 2 x Fmax)

choix = input('\nTaper "1" pour encoder, "2" pour décoder, "3" pour jouer et "4" pour enregistrer : ')

if choix == "1":
    texte, valence, k = encoder.demandeTexte()
    texte_binaire = encoder.transformationascii(texte)
    array = encoder.creation_array(texte_binaire, valence, k)
    encoder.array_vers_wav(array)
    print("Texte en binaire : ", texte_binaire, valence, k)
    print("Fréquences (Hz) :", np.linspace(Fmin, Fmax, valence))
    print(f"message.wav écrit : {len(array)} échantillons, {len(array) / fs:.1f} s")

elif choix == "2":
    valence = int(input("Valence utilisée à l'encodage (2, 4, 8, 16, 32) : "))
    print("Texte décodé :", decoder.decoder("messages/message.wav", valence))

elif choix == "3":
    jouer.jouer("messages/message.wav")

elif choix == "4":
    print("enregistrer")
else:
    print('Erreur : taper 1, 2, 3 ou 4')
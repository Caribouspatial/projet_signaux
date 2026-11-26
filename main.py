import numpy as np
import encoder, decoder, jouer, enregistrer

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
    choix2 = input('\nTaper "1" pour voir le message, "2" pour enregistrement : ')
    if choix2 == "1":
        valence = int(input("Valence utilisée à l'encodage (2, 4, 8, 16, 32) : "))
        print("Texte décodé :", decoder.decoder("messages/message.wav", valence))
    elif choix2 == "2":
        valence = int(input("Valence utilisée à l'encodage (2, 4, 8, 16, 32) : "))
        print("Texte décodé :", decoder.decoder("messages/enregistrement.wav", valence))
    else:
        print('erreur, taper "1" ou "2"')
elif choix == "3":

    choix2 = input('\nTaper "1" pour jouer le message, "2" pour enregistrement : ')
    if choix2 == "1":
        jouer.jouer("messages/message.wav")
    elif choix2 == "2":
        jouer.jouer("messages/enregistrement.wav")
    else:
        print('erreur, taper "1" ou "2"')

elif choix == "4":
    #print("Arrêter en entrant 'Enter' ou après 40 sec")
    enregistrer.enregistrer()
else:
    print('Erreur : taper 1, 2, 3 ou 4')
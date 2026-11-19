import os
import numpy as np
from scipy.io import wavfile
import encoder, decoder

Fmin = 500  # Hz
Fmax = 8000  # Hz
fs = 44000  # Hz : fréquence d'échantillonnage du .wav (doit être > 2 x Fmax)

DOSSIER_PROJET = os.path.dirname(os.path.abspath(__file__))
CHEMIN_WAV = os.path.join(DOSSIER_PROJET, "messages", "message.wav")

derniere_valence = decoder.VALENCE_DEFAUT

# Lanceur de code
choix = input('Taper "1" pour encoder, "2" pour decoder et "3" pour jouer le dernier texte encoder: ').strip()

if choix == "1":
    texte, valence, k = encoder.demandeTexte()
    derniere_valence = valence
    texte_binaire = encoder.transformationascii(texte)
    array = encoder.creation_array(texte_binaire, valence, k)
    chemin_genere = encoder.array_vers_wav(array, "message.wav")
    print("Texte en binaire : ", texte_binaire, valence, k)
    print("Fréquences (Hz) :", np.linspace(Fmin, Fmax, valence))
    print(f"Fichier écrit ({chemin_genere}) : {len(array)} échantillons, {len(array) / fs:.1f} s")
    debit_tonalites, debit_effectif = encoder.debits(valence)
    print(f"Débit pendant les tonalités : {debit_tonalites:.1f} bits/s | débit effectif (silences inclus) : {debit_effectif:.1f} bits/s")

elif choix == "2":
    if not os.path.exists(CHEMIN_WAV):
        print(f"Fichier introuvable : {CHEMIN_WAV}. Commence par taper '1' pour encoder un message.")
    else:
        rep = input(f"Valence utilisée à l'encodage [{derniere_valence}] : ").strip()
        valence = int(rep) if rep else derniere_valence
        message_decode = decoder.decoder(CHEMIN_WAV, valence)
        print("Message décodé :", message_decode)

elif choix == "3":
    if not os.path.exists(CHEMIN_WAV):
        print(f"Fichier introuvable : {CHEMIN_WAV}. Commence par taper '1' pour encoder un message.")
    else:
        try:
            import winsound
            print(f"Lecture de {CHEMIN_WAV}...")
            winsound.PlaySound(CHEMIN_WAV, winsound.SND_FILENAME)
        except ImportError:
            _, data = wavfile.read(CHEMIN_WAV)
            print(f"Fichier prêt ({len(data)} échantillons), lecture non supportée sur cet OS.")

else:
    print("Erreur taper 1, 2 ou 3")
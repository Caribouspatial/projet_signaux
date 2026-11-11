import encoder, decoder

#lanceur de code
choix = input('Taper "1"  pour encoder, "2" pour decoder et "3" pour jouer le dernier texte encoder: ')
if choix == "1":
    print("encoder choisis")
    texte, valence, k = encoder.demandeTexte()
    texte_binaire = encoder.transformationascii(texte)
    print("Texte en binaire : ", texte_binaire, valence, k)
elif choix == "2":
    print("décoder")
elif choix == "3":
    print("jouer .wav")
else:
    print("Erreur taper 1, 2 ou 3")
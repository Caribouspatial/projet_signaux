# Projet signaux
## Principes
Ce projet encode du texte en signaux audio M-FSK, puis peut décoder un message
à partir d'un fichier WAV.

1. Sur le PC 1, le texte est encodé dans un fichier `message.wav`.
2. Le fichier encodé est joué sur le PC 1.
3. Sur le PC 2, le son joué est enregistré dans un nouveau fichier `enregistrement.wav`.
4. Le fichier enregistré est décodé pour afficher le texte.

## Prérequis

Python 3 et les dépendances utilisées par le projet sont nécessaires :

```bash
pip install numpy scipy sounddevice matplotlib coverage
```

## Utilisation

### Ligne de commande

Le programme principal peut encore être lancé sans interface graphique :

```bash
python main.py
```

### Interface graphique

Lancer l'application avec :

```bash
python gui.py
```

## Tests unitaires

Pour exécuter tous les tests :

```bash
python unitest.py
```

## Arborescence

### main.py :
Fichier principal qui centralise tous les autres dans une interface de terminal à choix multiple.

### encoder.py :
Encode un texte saisi par l'utilisateur en signal audio M-FSK et l'enregistre dans `messages/message.wav` (voir `decoder.py`).

Principe, pour chaque lettre i (début à t = i * (ceil(8 / k) * Ts + espacement)) :
1. on convertit le caractère en ASCII binaire sur 8 bits, puis on le découpe en ceil(8 / k) groupes de k bits (complétés par des 0 à droite si nécessaire) -> son indice
2. on associe chaque indice à sa fréquence dans linspace(Fmin, Fmax, valence)
3. pour chaque tonalité, on génère une sinusoïde de durée Ts échantillonnée à fs, avec un fondu cosinus (rampe) au début et à la fin pour éviter les clics
4. on concatène les tonalités de la lettre, puis on assemble toutes les lettres séparées par un silence de durée espacement avant d'exporter le signal en `.wav` 16 bits mono

### decoder.py :
Décode un fichier `message.wav` encodé en M-FSK (voir `encoder.py`) et affiche le texte.

Principe, pour chaque lettre i (début à t = i * (ceil(8 / k) * TS + ESPACEMENT)) :
1. on découpe la lettre en ceil(8 / k) tonalités de durée TS chacune
2. pour chaque tonalité, on fait une FFT et on prend la fréquence dominante
3. on cherche la fréquence la plus proche dans linspace(FMIN, FMAX, valence) -> son indice
4. l'indice est écrit en binaire sur k bits ; on concatène, on garde 8 bits -> un caractère

### jouer.py :
Joue un fichier `.wav` 16 bits et attend la fin de la lecture.

### enregistrer.py :
Enregistre en brut l'entrée du micro et la fait passer par `nettoyer.py` avant de la sauvegarder dans `enregistrement.wav`.
### nettoyer.py :
Nettoie l'enregistrement du micro pour que `decoder.py` puisse mieux le lire.

`nettoyer(fichier)` remplace le fichier par sa version nettoyée.
Si aucun son n'est détecté, le fichier n'est PAS touché (rien n'est écrit, rien n'est copié)
et la fonction renvoie `False`.

Étapes (le signal n'est modifié que légèrement) :
1. stéréo -> mono, suppression de la composante continue
2. filtre passe-bande autour des fréquences utiles (FMIN..FMAX), sans déphasage
3. détection des lettres par "tonalité" : un son pur ressort même très faible, alors que
     le bruit et les clics (touche Entrée) n'en ont pas
4. début de chaque lettre recalé précisément sur la fréquence de sa 1re tonalité
5. fin du message = début de la dernière lettre + durée d'une lettre (la durée d'une lettre
     se déduit du pas entre lettres) ; complétée par du silence si l'enregistrement s'arrête trop tôt
6. recalage (1er son à t = 0), silences mis à zéro, chaque lettre ramenée au même volume
     (compense le gain automatique du micro)
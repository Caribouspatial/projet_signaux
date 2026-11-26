# Projet signaux
## Principes
Ce projet encode du texte en signaux audio M-FSK, puis peut décoder un message
à partir d'un fichier WAV.

1. Sur le PC 1, le texte est encodé en fichier `message.wav`.
2. Le fichier encodé est joué sur le PC 1.
3. Sur le PC 2, le son joué est enregistré dans un nouveau fichier `enregistrement.wav`.
4. Le fichier enregistré est decodé pour afficher le texte.

## Prérequis

Python 3 et les dépendances utilisées par le projet sont nécessaires :

```bash
pip install numpy scipy sounddevice matplotlib coverage
```

## Utilisation

### Ligne de commande

Le programme principal peut encore être lance sans interface graphique :

```bash
python main.py
```

### Interface graphique

Lancer l'application avec :

```bash
python gui.py
```

## Tests unitaires

Pour executé tous les tests :

```bash
python unitest.py
```

## Arborescence

### main.py:
Fichier principal qui centralise tous les autres dans une interface de terminal à choix multiple.
### encoder.py:

### decoder.py:
Décode un message.wav encodé en M-FSK (voir encodeur.py) et affiche le texte.

Principe, pour chaque lettre i (début à t = i * (ceil(8 / k) * TS + ESPACEMENT)) :
  1. on découpe la lettre en ceil(8 / k) tonalités de durée TS chacune
  2. pour chaque tonalité, on fait une FFT et on prend la fréquence dominante
  3. on cherche la fréquence la plus proche dans linspace(FMIN, FMAX, valence) -> son indice
  4. l'indice est écrit en binaire sur k bits ; on concatène, on garde 8 bits -> un caractère

### jouer.py:
Joue un .wav 16 bits et attend la fin de la lecture.

### enregistrer.py:

### nettoyer.py:
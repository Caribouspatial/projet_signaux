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
Enregistre en brut l'entrée du micro et la fait passer par nettoyer.py avant de le sauvgarder dans enregistrement.py
### nettoyer.py:
Nettoie un l'enregistrement du micro pour que decoder.py puisse mieux le lire.

nettoyer(fichier) remplace le fichier par sa version nettoyée.
Si aucun son n'est détecté, le fichier n'est PAS touché (rien n'est écrit, rien n'est copié)
et la fonction renvoie False.

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
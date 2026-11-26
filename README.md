# Projet signaux

## Principe

Ce projet encode du texte en signaux audio M-FSK, puis peut décoder un message
a partir d'un fichier WAV.

1. Sur le PC 1, le texte est encode en fichier `.wav`.
2. Le fichier encode est joue sur le PC 1.
3. Sur le PC 2, le son joue est enregistre dans un nouveau fichier `.wav`.
4. Le fichier enregistre est decode pour afficher le texte.

## Prerequis

Python 3 et les dependances utilisees par le projet sont necessaires :

```bash
pip install numpy scipy sounddevice matplotlib coverage
```

## Utilisation

### Ligne de commande

Le programme principal peut encore etre lance sans interface graphique :

```bash
python main.py
```

## Tests unitaires

Executer tous les tests :

```bash
python unitest.py
```

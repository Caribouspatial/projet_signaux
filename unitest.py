#!/usr/bin/env python3

import math
import os
import tempfile
import unittest
import wave

import numpy as np
from scipy.io import wavfile

import decoder
import encoder
import jouer
import nettoyer


class EncoderTests(unittest.TestCase):
    def test_ascii_conversion(self):
        self.assertEqual(
            encoder.transformationascii("A"),
            ["01000001"],
        )

    def test_symbol_slicing_with_padding(self):
        self.assertEqual(
            encoder.decoupage_symboles("01000001", 3),
            [2, 0, 2],
        )
        self.assertEqual(
            encoder.decoupage_symboles("01000001", 4),
            [4, 1],
        )

    def test_valid_and_invalid_valences(self):
        for valence, k in ((2, 1), (4, 2), (8, 3), (16, 4), (32, 5)):
            self.assertEqual(encoder.bits_par_symbole(valence), k)

        for valence in (0, 3, 6):
            with self.assertRaises(ValueError):
                encoder.bits_par_symbole(valence)

        with self.assertRaises(ValueError):
            decoder.decoder("missing.wav", 3)

    def test_theoretical_rates(self):
        tonalites, effectif = encoder.debits(4)
        self.assertAlmostEqual(tonalites, 2 / encoder.Ts)
        self.assertAlmostEqual(
            effectif,
            8 / (math.ceil(8 / 2) * encoder.Ts + encoder.espacement),
        )

    def test_created_array_size_and_amplitude(self):
        valence = 4
        k = encoder.bits_par_symbole(valence)
        binary = encoder.transformationascii("ABC")
        audio = encoder.creation_array(binary, valence, k)

        symbols_per_letter = math.ceil(8 / k)
        symbol_samples = int(round(encoder.Ts * encoder.fs))
        silence_samples = int(round(encoder.espacement * encoder.fs))
        expected_size = (
            len(binary) * symbols_per_letter * symbol_samples
            + (len(binary) - 1) * silence_samples
        )

        self.assertEqual(audio.shape, (expected_size,))
        self.assertEqual(audio.dtype, np.float32)
        self.assertGreaterEqual(float(audio.min()), -1.0)
        self.assertLessEqual(float(audio.max()), 1.0)

class WavAndDecoderTests(unittest.TestCase):
    def test_wav_round_trip_decodes_message(self):
        texte = "ABC"
        valence = 4
        k = encoder.bits_par_symbole(valence)
        binary = encoder.transformationascii(texte)
        audio = encoder.creation_array(binary, valence, k)

        with tempfile.TemporaryDirectory() as dossier:
            wav_path = os.path.join(dossier, "test_message.wav")
            pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2")
            with wave.open(wav_path, "wb") as fichier:
                fichier.setnchannels(1)
                fichier.setsampwidth(2)
                fichier.setframerate(encoder.fs)
                fichier.writeframes(pcm.tobytes())

            self.assertEqual(decoder.decoder(wav_path, valence), texte)

    def test_array_vers_wav_writes_valid_mono_wav(self):
        audio = np.zeros(1000, dtype=np.float32)
        with tempfile.TemporaryDirectory() as dossier:
            wav_path = os.path.join(dossier, "encoder_test.wav")
            encoder.array_vers_wav(audio, wav_path)

            with wave.open(wav_path, "rb") as fichier:
                self.assertEqual(fichier.getnchannels(), 1)
                self.assertEqual(fichier.getsampwidth(), 2)
                self.assertEqual(fichier.getframerate(), encoder.fs)
                self.assertEqual(fichier.getnframes(), len(audio))

    def test_decoder_rejects_non_power_of_two(self):
        with self.assertRaises(ValueError):
            decoder.decoder("missing.wav", 6)

    def test_decoder_ignores_empty_trailing_letter_segment(self):
        valence = 4
        audio = encoder.creation_array(
            encoder.transformationascii("AB"),
            valence,
            encoder.bits_par_symbole(valence),
        )
        audio = np.concatenate((audio, np.zeros(int(0.45 * encoder.fs))))

        with tempfile.TemporaryDirectory() as dossier:
            wav_path = os.path.join(dossier, "trailing_silence.wav")
            wavfile.write(
                wav_path,
                encoder.fs,
                (audio * 32767).astype(np.int16),
            )

            self.assertEqual(decoder.decoder(wav_path, valence), "AB")

    def test_dominant_frequency_rejects_empty_segment(self):
        with self.assertRaisesRegex(ValueError, "segment audio est vide"):
            decoder.frequence_dominante(np.array([]), encoder.fs)


class CleanerTests(unittest.TestCase):
    def test_silence_is_left_unchanged(self):
        sample_rate = 44100
        silence = np.zeros(sample_rate, dtype=np.int16)

        with tempfile.TemporaryDirectory() as dossier:
            wav_path = os.path.join(dossier, "silence.wav")
            wavfile.write(wav_path, sample_rate, silence)
            with open(wav_path, "rb") as fichier:
                original = fichier.read()

            self.assertFalse(nettoyer.nettoyer(wav_path))

            with open(wav_path, "rb") as fichier:
                self.assertEqual(fichier.read(), original)
            self.assertFalse(os.path.exists(wav_path + ".tmp.wav"))

    def test_active_tone_is_trimmed_and_normalized(self):
        sample_rate = 44100
        temps = np.arange(int(1.2 * sample_rate)) / sample_rate
        signal = np.zeros(len(temps), dtype=np.int16)
        actif = (temps >= 0.3) & (temps < 0.8)
        signal[actif] = (
            12000 * np.sin(2 * np.pi * 1800 * temps[actif])
        ).astype(np.int16)

        with tempfile.TemporaryDirectory() as dossier:
            wav_path = os.path.join(dossier, "recording.wav")
            wavfile.write(wav_path, sample_rate, signal)

            self.assertTrue(nettoyer.nettoyer(wav_path))

            output_rate, cleaned = wavfile.read(wav_path)
            self.assertEqual(output_rate, sample_rate)
            self.assertEqual(cleaned.dtype, np.int16)
            self.assertLess(len(cleaned), len(signal))
            self.assertGreater(int(np.max(np.abs(cleaned))), 20000)
            self.assertFalse(os.path.exists(wav_path + ".tmp.wav"))

    def test_weak_frequency_symbols_and_final_letter_are_preserved(self):
        texte = "test bonjour"
        valence = 4
        k = encoder.bits_par_symbole(valence)
        symboles_par_lettre = math.ceil(8 / k)
        nb_echantillons_symbole = int(round(encoder.Ts * encoder.fs))
        nb_silence = int(round(encoder.espacement * encoder.fs))
        audio = encoder.creation_array(
            encoder.transformationascii(texte), valence, k
        ).copy()

        for i, mot in enumerate(encoder.transformationascii(texte)):
            debut_lettre = i * (
                symboles_par_lettre * nb_echantillons_symbole + nb_silence
            )
            symboles = encoder.decoupage_symboles(mot, k)
            for j, symbole in enumerate(symboles):
                debut = debut_lettre + j * nb_echantillons_symbole
                fin = debut + nb_echantillons_symbole
                audio[debut:fin] *= {0: 0.07, 2: 0.0275}.get(symbole, 1.0)

        debut_enregistrement = int(0.1 * encoder.fs)
        enregistrement = np.pad(
            audio,
            (
                debut_enregistrement,
                60 * encoder.fs - debut_enregistrement - len(audio),
            ),
        )

        with tempfile.TemporaryDirectory() as dossier:
            wav_path = os.path.join(dossier, "weak_symbols.wav")
            wavfile.write(
                wav_path,
                encoder.fs,
                (enregistrement * 32767).astype(np.int16),
            )

            self.assertTrue(nettoyer.nettoyer(wav_path))
            self.assertEqual(decoder.decoder(wav_path, valence), texte)

    def test_short_message_in_long_recording_is_detected(self):
        valence = 2
        audio = encoder.creation_array(
            encoder.transformationascii("A"),
            valence,
            encoder.bits_par_symbole(valence),
        )
        debut_enregistrement = int(0.1 * encoder.fs)
        enregistrement = np.pad(
            audio,
            (
                debut_enregistrement,
                60 * encoder.fs - debut_enregistrement - len(audio),
            ),
        )

        with tempfile.TemporaryDirectory() as dossier:
            wav_path = os.path.join(dossier, "short_message.wav")
            wavfile.write(
                wav_path,
                encoder.fs,
                (enregistrement * 32767).astype(np.int16),
            )

            self.assertTrue(nettoyer.nettoyer(wav_path))
            self.assertEqual(decoder.decoder(wav_path, valence), "A")


if __name__ == "__main__":
    unittest.main()

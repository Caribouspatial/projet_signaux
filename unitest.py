#!/usr/bin/env python3

import math
import os
import tempfile
import unittest
import wave

import numpy as np

import decoder
import encoder
import jouer


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


if __name__ == "__main__":
    unittest.main()

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

if __name__ == "__main__":
    unittest.main()

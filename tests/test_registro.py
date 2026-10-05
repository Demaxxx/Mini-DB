"""Testes dos registros: cálculo de posição e conversão para bytes."""

import unittest

from source import (
    PAGE_SIZE,
    HEADER_SIZE,
    RECORD_SIZE,
    calcula_deslocamento,
    serializa_registro,
    desserializa_registro,
)


class TestRegistro(unittest.TestCase):

    def test_slot0_pagina2_comeca_no_byte_8208(self):
        self.assertEqual(calcula_deslocamento(2, 0), 8208)

    def test_formula_geral(self):
        self.assertEqual(
            calcula_deslocamento(3, 5),
            3 * PAGE_SIZE + HEADER_SIZE + 5 * RECORD_SIZE,
        )

    def test_valores_negativos_dao_erro(self):
        with self.assertRaises(ValueError):
            calcula_deslocamento(-1, 0)
        with self.assertRaises(ValueError):
            calcula_deslocamento(0, -1)

    def test_registro_tem_8_bytes(self):
        self.assertEqual(len(serializa_registro(42, 2026100)), 8)

    def test_ida_e_volta(self):
        dados = serializa_registro(42, 2026100)
        self.assertEqual(desserializa_registro(dados), (42, 2026100))

    def test_little_endian(self):
        # 1 em little-endian: o byte 01 vem primeiro
        self.assertEqual(serializa_registro(1, 0), b"\x01\x00\x00\x00\x00\x00\x00\x00")

    def test_tamanho_errado_da_erro(self):
        with self.assertRaises(ValueError):
            desserializa_registro(b"123")


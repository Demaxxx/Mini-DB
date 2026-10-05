"""Testes do M1: ler e gravar páginas no arquivo."""

import os
import tempfile
import unittest

from source import (
    PAGE_SIZE,
    SLOTS_POR_PAGINA,
    DiskStorage,
    grava_registro_slot,
    le_registro_slot,
)


class TestStorage(unittest.TestCase):

    def setUp(self):
        # Cria uma pasta temporária para o teste (é apagada no final)
        self.pasta = tempfile.TemporaryDirectory()
        self.caminho = os.path.join(self.pasta.name, "teste.db")

    def tearDown(self):
        self.pasta.cleanup()

    def test_arquivo_novo_comeca_vazio(self):
        with DiskStorage(self.caminho) as disco:
            self.assertEqual(disco.n_paginas, 0)

    def test_aloca_devolve_numeros_em_sequencia(self):
        with DiskStorage(self.caminho) as disco:
            self.assertEqual(disco.aloca(), 0)
            self.assertEqual(disco.aloca(), 1)
            self.assertEqual(disco.n_paginas, 2)

    def test_pagina_nova_tem_so_zeros(self):
        with DiskStorage(self.caminho) as disco:
            disco.aloca()
            self.assertEqual(disco.le(0), bytearray(PAGE_SIZE))

    def test_escreve_e_le(self):
        with DiskStorage(self.caminho) as disco:
            disco.aloca()
            pagina = bytearray(PAGE_SIZE)
            pagina[0:5] = b"ABCDE"
            disco.escreve(0, pagina)
            self.assertEqual(disco.le(0)[0:5], b"ABCDE")

    def test_tamanho_do_arquivo_e_multiplo_de_4096(self):
        with DiskStorage(self.caminho) as disco:
            disco.aloca()
            disco.aloca()
            disco.aloca()
        self.assertEqual(os.path.getsize(self.caminho), 3 * PAGE_SIZE)

    def test_escrever_pagina_com_tamanho_errado_da_erro(self):
        with DiskStorage(self.caminho) as disco:
            disco.aloca()
            with self.assertRaises(ValueError):
                disco.escreve(0, b"curto demais")

    def test_ler_pagina_que_nao_existe_da_erro(self):
        with DiskStorage(self.caminho) as disco:
            with self.assertRaises(IOError):
                disco.le(5)

    def test_numero_de_pagina_negativo_da_erro(self):
        with DiskStorage(self.caminho) as disco:
            disco.aloca()
            with self.assertRaises(ValueError):
                disco.le(-1)

    def test_dados_continuam_depois_de_fechar_e_abrir(self):
        with DiskStorage(self.caminho) as disco:
            grava_registro_slot(disco, 2, 0, 42, 2026100)

        with DiskStorage(self.caminho) as disco:
            self.assertEqual(disco.n_paginas, 3)
            self.assertEqual(le_registro_slot(disco, 2, 0), (42, 2026100))

    def test_registro_fica_no_byte_8208(self):
        with DiskStorage(self.caminho) as disco:
            grava_registro_slot(disco, 2, 0, 1, 2)

        with open(self.caminho, "rb") as arquivo:
            arquivo.seek(8208)
            self.assertEqual(arquivo.read(8), b"\x01\x00\x00\x00\x02\x00\x00\x00")

    def test_gravar_em_um_slot_nao_estraga_os_outros(self):
        with DiskStorage(self.caminho) as disco:
            grava_registro_slot(disco, 0, 0, 1, 10)
            grava_registro_slot(disco, 0, 1, 2, 20)
            self.assertEqual(le_registro_slot(disco, 0, 0), (1, 10))
            self.assertEqual(le_registro_slot(disco, 0, 1), (2, 20))

    def test_slot_negativo_da_erro_e_nao_mexe_no_cabecalho(self):
        with DiskStorage(self.caminho) as disco:
            disco.aloca()
            with self.assertRaises(ValueError):
                grava_registro_slot(disco, 0, -1, 7, 8)
            self.assertEqual(disco.le(0), bytearray(PAGE_SIZE))   # continua tudo zero

    def test_slot_grande_demais_da_erro(self):
        with DiskStorage(self.caminho) as disco:
            with self.assertRaises(ValueError):
                grava_registro_slot(disco, 0, SLOTS_POR_PAGINA, 1, 2)
            with self.assertRaises(ValueError):
                le_registro_slot(disco, 0, SLOTS_POR_PAGINA)

    def test_ultimo_slot_da_pagina_funciona(self):
        with DiskStorage(self.caminho) as disco:
            ultimo = SLOTS_POR_PAGINA - 1
            grava_registro_slot(disco, 0, ultimo, 9, 99)
            self.assertEqual(le_registro_slot(disco, 0, ultimo), (9, 99))

    def test_arquivo_com_tamanho_quebrado_da_erro(self):
        with open(self.caminho, "wb") as arquivo:
            arquivo.write(b"x" * 5000)       # 5000 não é múltiplo de 4096
        with self.assertRaises(ValueError):
            DiskStorage(self.caminho)


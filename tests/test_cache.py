"""Testes do M2: cache de páginas (LRU, páginas sujas, hits e misses)."""

import os
import tempfile
import unittest

from source import PAGE_SIZE, DiskStorage, BufferPool


class TestCache(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.caminho = os.path.join(self.pasta.name, "teste.db")
        self.disco = DiskStorage(self.caminho)
        for _ in range(4):
            self.disco.aloca()            # páginas 0, 1, 2 e 3

    def tearDown(self):
        self.disco.fecha()
        self.pasta.cleanup()

    def test_primeiro_acesso_e_miss_e_o_segundo_e_hit(self):
        cache = BufferPool(self.disco, capacidade=2)
        cache.get_page(0)
        self.assertEqual((cache.misses, cache.hits), (1, 0))
        cache.get_page(0)
        self.assertEqual((cache.misses, cache.hits), (1, 1))

    def test_taxa_de_acerto(self):
        cache = BufferPool(self.disco, capacidade=2)
        self.assertEqual(cache.hit_ratio, 0.0)     # ainda sem acessos
        cache.get_page(0)
        cache.get_page(0)
        self.assertEqual(cache.hit_ratio, 0.5)

    def test_capacidade_invalida_da_erro(self):
        with self.assertRaises(ValueError):
            BufferPool(self.disco, capacidade=0)

    def test_sai_a_pagina_menos_recente(self):
        cache = BufferPool(self.disco, capacidade=2)
        cache.get_page(0)
        cache.get_page(1)
        cache.get_page(0)      # a 0 ficou mais recente que a 1
        cache.get_page(2)      # cache cheio: tem que sair a página 1
        self.assertNotIn(1, cache)
        self.assertIn(0, cache)
        self.assertIn(2, cache)
        self.assertEqual(len(cache), 2)

    def test_pagina_suja_vai_para_o_disco_quando_sai_do_cache(self):
        cache = BufferPool(self.disco, capacidade=1)
        cache.get_page(0)[0:3] = b"abc"
        cache.mark_dirty(0)
        cache.get_page(1)      # a página 0 sai do cache e deve ser gravada
        self.assertEqual(self.disco.le(0)[0:3], b"abc")

    def test_pagina_limpa_nao_precisa_ser_gravada(self):
        cache = BufferPool(self.disco, capacidade=1)
        cache.get_page(0)[0:3] = b"abc"      # alterou, mas NÃO chamou mark_dirty
        cache.get_page(1)
        self.assertEqual(self.disco.le(0)[0:3], b"\x00\x00\x00")

    def test_alteracao_so_chega_no_disco_depois_do_flush(self):
        cache = BufferPool(self.disco, capacidade=4)
        cache.get_page(2)[0:2] = b"ok"
        cache.mark_dirty(2)
        self.assertEqual(self.disco.le(2)[0:2], b"\x00\x00")   # ainda não gravou
        cache.flush()
        self.assertEqual(self.disco.le(2)[0:2], b"ok")
        self.assertEqual(cache.dirty_pages, set())

    def test_write_page_troca_a_pagina_e_marca_como_suja(self):
        cache = BufferPool(self.disco, capacidade=4)
        nova = bytes([7]) * PAGE_SIZE
        cache.write_page(1, nova)
        self.assertEqual(cache.dirty_pages, {1})
        cache.flush_page(1)
        self.assertEqual(self.disco.le(1), bytearray(nova))

    def test_write_page_com_tamanho_errado_da_erro(self):
        cache = BufferPool(self.disco, capacidade=4)
        with self.assertRaises(ValueError):
            cache.write_page(0, b"curto")

    def test_mark_dirty_de_pagina_fora_do_cache_da_erro(self):
        cache = BufferPool(self.disco, capacidade=4)
        with self.assertRaises(KeyError):
            cache.mark_dirty(0)

    def test_evict_grava_a_pagina_suja_e_tira_do_cache(self):
        cache = BufferPool(self.disco, capacidade=4)
        cache.get_page(3)[0:1] = b"Z"
        cache.mark_dirty(3)
        cache.evict(3)
        self.assertNotIn(3, cache)
        self.assertEqual(self.disco.le(3)[0:1], b"Z")

    def test_clear_esvazia_o_cache_sem_perder_dados(self):
        cache = BufferPool(self.disco, capacidade=4)
        cache.get_page(0)[0:1] = b"Q"
        cache.mark_dirty(0)
        cache.clear()
        self.assertEqual(len(cache), 0)
        self.assertEqual(self.disco.le(0)[0:1], b"Q")

    def test_pedir_pagina_que_nao_existe_nao_estraga_o_cache(self):
        cache = BufferPool(self.disco, capacidade=1)
        cache.get_page(0)[0:1] = b"K"
        cache.mark_dirty(0)
        with self.assertRaises(IOError):
            cache.get_page(99)
        # A página 0 continua no cache, ainda suja, e o miss não foi contado
        self.assertIn(0, cache)
        self.assertEqual(cache.dirty_pages, {0})
        self.assertEqual(cache.misses, 1)

    def test_with_grava_tudo_ao_sair(self):
        with BufferPool(self.disco, capacidade=2) as cache:
            cache.get_page(0)[0:4] = b"fim!"
            cache.mark_dirty(0)

        # O "with" fechou o disco; abrimos de novo para conferir o arquivo
        with DiskStorage(self.caminho) as outro:
            self.assertEqual(outro.le(0)[0:4], b"fim!")



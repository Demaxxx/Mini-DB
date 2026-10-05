"""M2 - Buffer Pool (cache de páginas na memória).

Ler do disco é LENTO e ler da memória RAM é RÁPIDO. Então guardamos
algumas páginas na memória para não precisar ir ao disco toda hora.

Regras desse cache:
- Ele guarda no máximo `capacidade` páginas (padrão: 8).
- Quando enche, sai a página que ficou mais tempo sem ser usada (LRU).
- Páginas alteradas ficam marcadas como "sujas" e só vão para o disco
  mais tarde (quando saem do cache ou quando chamamos flush).
"""

from .storage import PAGE_SIZE


class BufferPool:
    """Cache de páginas com política LRU (Least Recently Used)."""

    def __init__(self, pager, capacidade=8):
        if capacidade <= 0:
            raise ValueError("A capacidade precisa ser maior que zero")

        self.pager = pager            # o DiskStorage que fica "atrás" do cache
        self.capacidade = capacidade

        self.paginas = {}             # número da página -> conteúdo (bytearray)
        self.sujas = set()            # números das páginas alteradas (dirty)
        self.ordem = []               # ordem de uso: a MAIS ANTIGA fica na frente

        self.hits = 0                 # vezes que a página já estava no cache
        self.misses = 0               # vezes que precisou buscar no disco

    # ------------------------------------------------------------------
    # Funções auxiliares (uso interno)
    # ------------------------------------------------------------------

    def _valida(self, pagina):
        if not isinstance(pagina, int) or pagina < 0:
            raise ValueError(f"Número de página inválido: {pagina}")

    def _marca_como_usada(self, pagina):
        """Coloca a página no FIM da lista (a mais recente)."""
        self.ordem.remove(pagina)
        self.ordem.append(pagina)

    def _grava_se_suja(self, pagina):
        """Se a página foi alterada, grava no disco e tira a marca de suja."""
        if pagina in self.sujas:
            self.pager.escreve(pagina, self.paginas[pagina])
            self.sujas.remove(pagina)

    # ------------------------------------------------------------------
    # Funções principais
    # ------------------------------------------------------------------

    def get_page(self, pagina):
        """Devolve o conteúdo da página (do cache ou, se preciso, do disco)."""
        self._valida(pagina)

        # Acerto (hit): a página já está na memória
        if pagina in self.paginas:
            self.hits += 1
            self._marca_como_usada(pagina)
            return self.paginas[pagina]

        # Falha (miss): busca no disco primeiro.
        # Se der erro (página inexistente), o cache continua intacto.
        conteudo = self.pager.le(pagina)
        self.misses += 1

        # Cache cheio? Tira a página que está há mais tempo sem uso
        if len(self.paginas) >= self.capacidade:
            mais_antiga = self.ordem.pop(0)
            self._grava_se_suja(mais_antiga)    # não perde alterações
            del self.paginas[mais_antiga]

        self.paginas[pagina] = conteudo
        self.ordem.append(pagina)
        return conteudo

    def mark_dirty(self, pagina):
        """Avisa que a página foi alterada na memória (precisa ir para o disco)."""
        self._valida(pagina)
        if pagina not in self.paginas:
            raise KeyError(f"A página {pagina} não está no cache")
        self.sujas.add(pagina)

    def write_page(self, pagina, dados):
        """Troca o conteúdo inteiro da página (4096 bytes) e marca como suja."""
        self._valida(pagina)
        if len(dados) != PAGE_SIZE:
            raise ValueError(
                f"A página precisa ter {PAGE_SIZE} bytes, mas recebi {len(dados)}"
            )

        self.get_page(pagina)                    # garante que ela está no cache
        self.paginas[pagina][:] = dados          # [:] troca o conteúdo sem criar outro objeto
        self.sujas.add(pagina)

    def flush_page(self, pagina):
        """Grava UMA página no disco (se ela estiver suja)."""
        self._valida(pagina)
        if pagina not in self.paginas:
            raise KeyError(f"A página {pagina} não está no cache")
        self._grava_se_suja(pagina)

    def flush(self):
        """Grava TODAS as páginas sujas no disco e confirma com sync."""
        for pagina in list(self.sujas):          # list() porque o set muda no meio do loop
            self._grava_se_suja(pagina)
        self.pager.sync()

    def evict(self, pagina):
        """Tira uma página do cache (antes grava, se estiver suja)."""
        self._valida(pagina)
        if pagina not in self.paginas:
            return

        self._grava_se_suja(pagina)
        del self.paginas[pagina]
        self.ordem.remove(pagina)

    def clear(self):
        """Grava tudo que está sujo e esvazia o cache."""
        self.flush()
        self.paginas.clear()
        self.ordem.clear()

    def close(self):
        """Grava tudo e fecha o arquivo do disco."""
        self.flush()
        self.pager.fecha()

    # ------------------------------------------------------------------
    # Informações úteis
    # ------------------------------------------------------------------

    def contains(self, pagina):
        """True se a página está no cache agora."""
        return pagina in self.paginas

    def __contains__(self, pagina):     # permite escrever:  3 in cache
        return self.contains(pagina)

    def __len__(self):                  # permite escrever:  len(cache)
        return len(self.paginas)

    @property
    def dirty_pages(self):
        """Conjunto com os números das páginas sujas."""
        return set(self.sujas)

    @property
    def hit_ratio(self):
        """Taxa de acerto: hits / (hits + misses). Vai de 0.0 até 1.0."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    # Permite usar:  with BufferPool(disco) as cache: ...
    def __enter__(self):
        return self

    def __exit__(self, tipo, valor, erro):
        self.close()


# Outro nome para a mesma classe (usado no enunciado da disciplina)
PageCache = BufferPool
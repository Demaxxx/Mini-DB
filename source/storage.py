"""M1 - Armazenamento em disco (Pager).

Ideia principal: o arquivo do banco é dividido em "páginas" (blocos) de
4096 bytes. Para ler ou gravar, sempre mexemos numa página inteira.

Cada página tem:
    [ cabeçalho: 16 bytes ][ slot 0: 8 bytes ][ slot 1: 8 bytes ] ...

Cada registro (slot) guarda dois números: id e matrícula (4 bytes cada).
"""

import os
import struct

PAGE_SIZE = 4096     # tamanho de cada página, em bytes
HEADER_SIZE = 16     # bytes reservados no começo da página (ainda não usados)
RECORD_SIZE = 8      # tamanho de um registro: 2 números de 4 bytes

# Quantos registros cabem em uma página: (4096 - 16) // 8 = 510
SLOTS_POR_PAGINA = (PAGE_SIZE - HEADER_SIZE) // RECORD_SIZE

# "<II" = dois números inteiros sem sinal (I), de 4 bytes cada,
# com o byte menos importante primeiro (< = little-endian)
FORMATO_REGISTRO = "<II"


# ----------------------------------------------------------------------
# Funções de registro
# ----------------------------------------------------------------------

def calcula_deslocamento(pagina, slot):
    """Diz em qual byte do ARQUIVO começa o registro (pagina, slot).

    Fórmula: pagina * 4096 + 16 + slot * 8
    Exemplo: pagina 2, slot 0 -> 2 * 4096 + 16 + 0 = 8208
    """
    if pagina < 0 or slot < 0:
        raise ValueError("pagina e slot não podem ser negativos")
    return pagina * PAGE_SIZE + HEADER_SIZE + slot * RECORD_SIZE


def serializa_registro(id_aluno, matricula):
    """Transforma dois números em 8 bytes (para guardar no arquivo)."""
    return struct.pack(FORMATO_REGISTRO, id_aluno, matricula)


def desserializa_registro(dados):
    """Faz o caminho contrário: 8 bytes viram (id_aluno, matricula)."""
    if len(dados) != RECORD_SIZE:
        raise ValueError(
            f"Um registro precisa ter {RECORD_SIZE} bytes, mas recebi {len(dados)}"
        )
    return struct.unpack(FORMATO_REGISTRO, dados)


def confere_slot(slot):
    """Garante que o slot existe dentro de uma página (0 até 509)."""
    if slot < 0 or slot >= SLOTS_POR_PAGINA:
        raise ValueError(
            f"Slot inválido: {slot}. Use um valor de 0 até {SLOTS_POR_PAGINA - 1}"
        )


# ----------------------------------------------------------------------
# Classe que mexe no arquivo
# ----------------------------------------------------------------------

class DiskStorage:
    """Lê e grava páginas de 4096 bytes em um arquivo."""

    def __init__(self, caminho):
        self.caminho = str(caminho)

        # Cria a pasta do arquivo, se ela ainda não existir
        pasta = os.path.dirname(self.caminho)
        if pasta:
            os.makedirs(pasta, exist_ok=True)

        # "r+b" abre um arquivo que já existe (ler e escrever).
        # "w+b" cria um arquivo novo.
        if os.path.exists(self.caminho):
            self.arquivo = open(self.caminho, "r+b")
        else:
            self.arquivo = open(self.caminho, "w+b")

        # Descobre o tamanho do arquivo indo até o final dele
        self.arquivo.seek(0, os.SEEK_END)
        tamanho = self.arquivo.tell()

        # Um arquivo de páginas completas tem tamanho múltiplo de 4096
        if tamanho % PAGE_SIZE != 0:
            self.arquivo.close()
            raise ValueError(
                f"Arquivo corrompido: {tamanho} bytes não é múltiplo de {PAGE_SIZE}"
            )

        self.n_paginas = tamanho // PAGE_SIZE

    def _confere_pagina(self, numero_pagina):
        if not isinstance(numero_pagina, int) or numero_pagina < 0:
            raise ValueError(f"Número de página inválido: {numero_pagina}")

    def le(self, numero_pagina):
        """Lê uma página do disco e devolve seus 4096 bytes (bytearray)."""
        self._confere_pagina(numero_pagina)

        self.arquivo.seek(numero_pagina * PAGE_SIZE)   # vai até o começo da página
        bloco = self.arquivo.read(PAGE_SIZE)

        # Se a página não existe, o arquivo acaba antes e vem menos de 4096 bytes
        if len(bloco) != PAGE_SIZE:
            raise IOError(f"Não consegui ler a página {numero_pagina}: ela não existe no arquivo")

        # bytearray pode ser alterado; bytes normal não pode
        return bytearray(bloco)

    def escreve(self, numero_pagina, conteudo):
        """Grava uma página no disco. O conteúdo precisa ter 4096 bytes."""
        self._confere_pagina(numero_pagina)

        if len(conteudo) != PAGE_SIZE:
            raise ValueError(
                f"A página precisa ter {PAGE_SIZE} bytes, mas recebi {len(conteudo)}"
            )

        self.arquivo.seek(numero_pagina * PAGE_SIZE)
        self.arquivo.write(conteudo)

        # Se gravou depois da última página, o arquivo cresceu
        if numero_pagina >= self.n_paginas:
            self.n_paginas = numero_pagina + 1

    def aloca(self):
        """Cria uma página nova (só zeros) no fim do arquivo e devolve o número dela."""
        numero = self.n_paginas
        self.escreve(numero, bytes(PAGE_SIZE))   # bytes(4096) = 4096 zeros
        return numero

    def sync(self):
        """Garante que tudo que foi gravado já está mesmo no disco.

        flush() manda os dados do Python para o sistema operacional.
        fsync() manda do sistema operacional para o disco de verdade.
        Sem o fsync, uma queda de energia poderia perder os dados.
        """
        if not self.arquivo.closed:
            self.arquivo.flush()
            os.fsync(self.arquivo.fileno())

    def fecha(self):
        """Salva tudo no disco e fecha o arquivo."""
        if not self.arquivo.closed:
            self.sync()
            self.arquivo.close()

    # Permite usar:  with DiskStorage("arquivo.db") as disco: ...
    # O arquivo é fechado sozinho no final do bloco "with".
    def __enter__(self):
        return self

    def __exit__(self, tipo, valor, erro):
        self.fecha()


# Outro nome para a mesma classe (usado no enunciado da disciplina)
Pager = DiskStorage


# ----------------------------------------------------------------------
# Gravar e ler um registro em (página, slot)
# ----------------------------------------------------------------------

def grava_registro_slot(storage, numero_pagina, slot, id_registro, matricula):
    """Grava um registro (id, matrícula) no slot de uma página."""
    confere_slot(slot)

    # Se a página ainda não existe, cria páginas até chegar nela
    while storage.n_paginas <= numero_pagina:
        storage.aloca()

    pagina = storage.le(numero_pagina)
    inicio = HEADER_SIZE + slot * RECORD_SIZE       # posição dentro da página
    pagina[inicio:inicio + RECORD_SIZE] = serializa_registro(id_registro, matricula)
    storage.escreve(numero_pagina, pagina)
    storage.sync()


def le_registro_slot(storage, numero_pagina, slot):
    """Lê o registro (id, matrícula) que está no slot de uma página."""
    confere_slot(slot)

    pagina = storage.le(numero_pagina)
    inicio = HEADER_SIZE + slot * RECORD_SIZE
    return desserializa_registro(pagina[inicio:inicio + RECORD_SIZE])
import os
import struct

PAGE_SIZE = 4096 # tamanho de cada página (bloco) em bytes
HEADER_SIZE = 16 # espaço reservado no início da página
RECORD_SIZE = 8 # tamanho de cada registro

def escreve_pagina(caminho, n, dados):
    """escreve exatamente 4096 bytes na página n do arquivo."""
    if len(dados) != PAGE_SIZE:
        raise ValueError(f"esperado {PAGE_SIZE} bytes, recebi {len(dados)}")

    # "r+b" = abre um arquivo binário existente para leitura E escrita
    # se o arquivo não existe, cria um vazio
    if not os.path.exists(caminho):
        open(caminho, "wb").close()

    with open(caminho, "r+b") as f:
        f.seek(n * PAGE_SIZE)   # pula para o início da página n
        f.write(dados)


def le_pagina(caminho, n):
    """lê os 4096 bytes da página n do arquivo."""
    with open(caminho, "rb") as f:
        f.seek(n * PAGE_SIZE)
        dados = f.read(PAGE_SIZE)
    return dados

def calcula_offset(pagina, slot):
    return (pagina * PAGE_SIZE) + HEADER_SIZE + (slot * RECORD_SIZE)

def grava_registro(caminho, pagina, slot, dados):
    if len(dados) != RECORD_SIZE:
        raise ValueError(f"registro deve ter {RECORD_SIZE} bytes")

    if not os.path.exists(caminho):
        open(caminho, "wb").close()

    with open(caminho, "r+b") as f:
        offset = calcula_offset(pagina, slot)
        f.seek(offset)
        f.write(dados)


def le_registro(caminho, pagina, slot):
    with open(caminho, "rb") as f:
        offset = calcula_offset(pagina, slot)
        f.seek(offset)
        dados = f.read(RECORD_SIZE)
    return dados

# TESTES
if __name__ == "__main__":
    caminho = "minidb.db"

    # um registro qualquer de 8 bytes
    registro = struct.pack('<II', 42, 100)

    grava_registro(caminho, pagina=2, slot=0, dados=registro)

    lido = le_registro(caminho, pagina=2, slot=0)
    print(struct.unpack('<II', lido))

print(calcula_offset(2, 0))


def escreve_cabecalho(pagina_bytes, n_registros):
    """escreve n_registros (4 bytes) no início dos 16 bytes de cabeçalho."""
    header = struct.pack('<I', n_registros) # 4 bytes usados
    header += bytes(HEADER_SIZE - len(header)) # completa até 16 com zeros
    pagina_bytes[0:HEADER_SIZE] = header
    return pagina_bytes


def le_cabecalho(pagina_bytes):
    """lê os 16 bytes de cabeçalho e devolve n_registros."""
    (n_registros,) = struct.unpack('<I', pagina_bytes[0:4])
    return n_registros


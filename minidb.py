"""MiniDB - demonstração dos módulos M1 e M2.

Para rodar:   python minidb.py

O código do banco fica na pasta source/:
- source/storage.py -> M1: páginas e arquivo em disco
- source/cache.py   -> M2: cache de páginas (Buffer Pool)
"""

import os

from source import (
    PAGE_SIZE,
    HEADER_SIZE,
    RECORD_SIZE,
    DiskStorage,
    BufferPool,
    calcula_deslocamento,
    grava_registro_slot,
    le_registro_slot,
)


def mostra_hexadecimal(caminho, inicio=8192, quantidade=32):
    """Mostra os bytes do arquivo em hexadecimal (como um editor hex faria)."""
    print(f"\n--- Bytes de {caminho} (do byte {inicio} ao {inicio + quantidade}) ---")
    with open(caminho, "rb") as arquivo:
        arquivo.seek(inicio)
        dados = arquivo.read(quantidade)

    # Mostra 16 bytes por linha
    for i in range(0, len(dados), 16):
        linha = dados[i:i + 16]
        hexa = " ".join(f"{b:02x}" for b in linha)
        texto = "".join(chr(b) if 32 <= b < 127 else "." for b in linha)
        print(f"{inicio + i:08x}  {hexa:<48}  |{texto}|")


def demonstracao_m1():
    print("=" * 60)
    print("M1 - Armazenamento em disco (páginas)")
    print("=" * 60)

    caminho = os.path.join("data", "minidb_demo_m1.db")
    if os.path.exists(caminho):
        os.remove(caminho)          # começa sempre do zero

    print(f"1. Criando o arquivo '{caminho}'...")
    disco = DiskStorage(caminho)
    print(f"   Páginas no começo: {disco.n_paginas}")

    print("   Criando páginas até chegar na página 2...")
    while disco.n_paginas <= 2:
        numero = disco.aloca()
        print(f"   -> Página {numero} criada (4096 bytes zerados)")

    id_aluno = 42
    matricula = 2026100
    print(f"\n2. Gravando no slot 0 da página 2: id={id_aluno}, matrícula={matricula}")
    grava_registro_slot(disco, 2, 0, id_aluno, matricula)

    offset = calcula_deslocamento(2, 0)
    print(f"   Posição no arquivo: 2 * {PAGE_SIZE} + {HEADER_SIZE} + 0 * {RECORD_SIZE} = {offset}")

    print("\n3. Fechando e abrindo o arquivo de novo (como se o programa reiniciasse)...")
    disco.fecha()
    disco = DiskStorage(caminho)

    id_lido, matricula_lida = le_registro_slot(disco, 2, 0)
    print(f"   Lido do disco: id={id_lido}, matrícula={matricula_lida}")

    if id_lido == id_aluno and matricula_lida == matricula:
        print("   [OK] Os dados continuaram no arquivo!")
    else:
        print("   [ERRO] Os dados lidos são diferentes dos gravados!")

    mostra_hexadecimal(caminho)
    disco.fecha()


def demonstracao_m2():
    print("\n" + "=" * 60)
    print("M2 - Cache de páginas (Buffer Pool com LRU)")
    print("=" * 60)

    caminho = os.path.join("data", "minidb_demo_m2.db")
    if os.path.exists(caminho):
        os.remove(caminho)

    disco = DiskStorage(caminho)
    for _ in range(3):
        disco.aloca()               # 3 páginas: 0, 1 e 2

    print("1. Criando um cache que guarda no máximo 2 páginas")
    cache = BufferPool(disco, capacidade=2)

    print("\n2. Pedindo a página 0 pela primeira vez:")
    cache.get_page(0)
    print(f"   misses={cache.misses}, hits={cache.hits}  (veio do disco: miss)")

    print("\n3. Pedindo a página 0 de novo:")
    cache.get_page(0)
    print(f"   misses={cache.misses}, hits={cache.hits}  (já estava na memória: hit)")

    print("\n4. Alterando a página 0 na memória...")
    pagina0 = cache.get_page(0)
    pagina0[:8] = b"DEMO_M2!"
    cache.mark_dirty(0)
    print(f"   Páginas sujas: {cache.dirty_pages}")

    print("\n5. Pedindo a página 1:")
    cache.get_page(1)
    print(f"   Páginas no cache: {cache.ordem}  (a mais antiga vem primeiro)")

    print("\n6. Usando a página 0 de novo (ela vira a mais recente):")
    cache.get_page(0)
    print(f"   Ordem de uso: {cache.ordem}")

    print("\n7. Pedindo a página 2 (cache cheio! sai a menos usada: a página 1):")
    cache.get_page(2)
    print(f"   Páginas no cache: {cache.ordem}")
    print(f"   A página 1 está no cache? {cache.contains(1)} (deve ser False)")
    print(f"   A página 0 está no cache? {cache.contains(0)} (deve ser True)")

    print(f"\n8. Taxa de acerto: {cache.hit_ratio:.0%}")

    print("\n9. Fechando o cache (grava as páginas sujas no disco)...")
    cache.close()

    # Confere se a alteração da página 0 realmente foi para o arquivo
    with open(caminho, "rb") as arquivo:
        primeiros_bytes = arquivo.read(8)
    if primeiros_bytes == b"DEMO_M2!":
        print("   [OK] A alteração da página 0 foi gravada no disco!")
    else:
        print("   [ERRO] A alteração não chegou no disco!")


if __name__ == "__main__":
    demonstracao_m1()
    demonstracao_m2()
    print("\n" + "=" * 60)
    print("Demonstrações concluídas!")
    print("=" * 60)
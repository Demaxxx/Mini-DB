# MiniDB — um banco de dados feito do zero em Python 

## Discentes Edimax Bastos e Emanoel Neto

Projeto da disciplina de **Banco de Dados II**. A ideia é entender como um banco de dados funciona "por dentro", construindo um pedacinho de cada vez.

---

## O que já está pronto

| Módulo | O que faz | Status |
|--------|-----------|--------|
| **M1** | Guarda e lê dados em um arquivo, dividido em páginas de 4096 bytes | Pronto |
| **M2** | Cache na memória (Buffer Pool) para não ler o disco toda hora | Pronto |
| M3 | Índice em Árvore B+ | A fazer |
| M4 | Leitura de comandos SQL e catálogo de tabelas | A fazer |
| M5 | Execução das consultas | A fazer |
| M6 | Transações (`BEGIN`, `COMMIT`, `ROLLBACK`) | A fazer |
| M7 | Recuperação de falhas (log WAL) | A fazer |

---

## Como funciona 

### M1 — Páginas

O banco não guarda os dados "soltos" no arquivo. O arquivo é dividido em **páginas**, que são blocos de tamanho fixo: **4096 bytes** (4 KB).

Pense num caderno: cada folha é uma página. Para achar uma informação, você vai direto na folha certa, sem precisar ler o caderno inteiro.

```text
Arquivo:  | Página 0 | Página 1 | Página 2 | Página 3 | ...
            4096 B     4096 B     4096 B     4096 B
```

Dentro de cada página:

```text
| cabeçalho (16 bytes) | slot 0 (8 bytes) | slot 1 (8 bytes) | slot 2 ... |
```

- **Cabeçalho**: 16 bytes reservados no começo. (Por enquanto estão reservados, mas ainda não guardam nada.)
- **Slot**: um "espacinho" para um registro. Cada registro tem **8 bytes**: o `id` (4 bytes) e a `matrícula` (4 bytes).
- Cabem **510 registros** por página: (4096 − 16) ÷ 8 = 510.

**Em que byte do arquivo começa um registro?**

```text
byte = (página × 4096) + 16 + (slot × 8)
```

Exemplo: slot 0 da página 2 → `2 × 4096 + 16 + 0 × 8` = **8208**.

### M2 — Cache (Buffer Pool)

Ler do disco é **lento**; ler da memória RAM é **rápido**. Então o cache guarda algumas páginas na memória:

- **Hit** (acerto): a página já estava no cache. Rápido!
- **Miss** (falha): a página não estava, então foi buscada no disco.
- **LRU** (*Least Recently Used*, "menos usada recentemente"): quando o cache enche, sai a página que está há mais tempo sem ser usada.
- **Página suja (dirty)**: página que foi alterada na memória, mas ainda não foi gravada no disco. Quando uma página suja sai do cache, ela é gravada antes, para não perdermos nada.

---

## Estrutura das pastas

```text
Mini-DB/
├── source/              # O código do banco
│   ├── __init__.py
│   ├── storage.py       # M1: páginas, arquivo e registros
│   └── cache.py         # M2: cache de páginas
├── tests/               # Testes automáticos
│   ├── test_registro.py
│   ├── test_storage.py
│   └── test_cache.py
├── notes/               # Anotações de cada módulo
│   ├── M1.md
│   └── M2.md
├── data/                # Arquivos .db criados pela demonstração
├── minidb.py            # Demonstração (é só rodar)
├── notes.md             # Resposta da questão dos bytes (8208)
└── README.md            # Este arquivo
```

---

## Como rodar

Precisa do **Python 3.10 ou mais novo**. Abra o terminal dentro da pasta `Mini-DB`.

**Demonstração** (mostra tudo funcionando, passo a passo):

```bash
python minidb.py
```

**Testes** (conferem se tudo continua funcionando):

```bash
python -m unittest discover -s tests -t . -v
```

Se você tiver o `pytest` instalado, também funciona:

```bash
pytest tests -v
```

---

## Exemplo de uso no código

```python
from source import DiskStorage, BufferPool, grava_registro_slot, le_registro_slot

# M1: gravar e ler um registro
disco = DiskStorage("data/meu_banco.db")
grava_registro_slot(disco, 2, 0, 42, 2026100)    # página 2, slot 0: id=42, matrícula=2026100
print(le_registro_slot(disco, 2, 0))              # (42, 2026100)

# M2: usar o cache
cache = BufferPool(disco, capacidade=4)
pagina = cache.get_page(0)       # busca a página 0 (do disco ou da memória)
pagina[0:3] = b"abc"             # altera na memória
cache.mark_dirty(0)              # avisa que ela foi alterada
cache.close()                    # grava tudo e fecha o arquivo
```

---

## Dicionário rápido

| Palavra | Significa |
|---------|-----------|
| **Página** | Bloco de 4096 bytes do arquivo |
| **Slot** | Espaço de um registro dentro da página |
| **Offset / deslocamento** | Posição (em bytes) a partir do começo do arquivo |
| **Registro / tupla** | Uma "linha" de dados (aqui: id + matrícula) |
| **Little-endian** | Jeito de guardar números em que o byte menos importante vem primeiro |
| **fsync** | Comando que força o sistema a gravar de verdade no disco |
| **Cache** | Cópia na memória de dados que estão no disco |

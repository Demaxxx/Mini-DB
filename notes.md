# Anotações — MiniDB

## Pergunta (M1)

> Páginas de 4096 bytes, cabeçalho de 16 bytes e registros de 8 bytes.
> **Em qual byte do arquivo começa o registro do slot 0 da página 2?**

## Resposta

**Byte 8208.** O registro ocupa do byte 8208 até o byte 8215 (são 8 bytes).

## Como chegar nesse número

1. **Onde começa a página 2?**
   A contagem começa do zero: antes da página 2 existem a página 0 e a página 1.
   `2 × 4096 = 8192`

2. **Pular o cabeçalho.**
   Os primeiros 16 bytes da página são o cabeçalho.
   `8192 + 16 = 8208`

3. **Pular os registros anteriores.**
   O slot 0 é o primeiro, então não tem nenhum registro antes dele.
   `0 × 8 = 0`

4. **Somar tudo.**
   `8192 + 16 + 0 = 8208`

Fórmula geral (está na função `calcula_deslocamento(pagina, slot)`):

```text
byte = (pagina × 4096) + 16 + (slot × 8)
```

## Desenho da página 2

```text
Byte do arquivo:  8192          8208        8216        8224           12287
                   |            |           |           |               |
                   [ cabeçalho ][ slot 0   ][ slot 1   ][ slot 2 ... vazio ]
                     16 bytes     8 bytes     8 bytes
                                  ^
                                  aqui começa o registro (id + matrícula)
```

## Teste feito

- Gravei o registro `id = 42` e `matrícula = 2026100` no slot 0 da página 2.
- Fechei o arquivo e abri de novo (como se o programa tivesse reiniciado).
- Li os bytes 8208 a 8215 e o resultado foi o mesmo registro. Funcionou.
- Dá para ver isso rodando `python minidb.py`: ele mostra os bytes em hexadecimal.

## M2 — Cache, em resumo

- O `BufferPool` fica entre o programa e o disco e guarda até **8 páginas** na memória (esse é o padrão).
- **Hit**: a página já estava na memória. **Miss**: precisou buscar no disco.
- Quando o cache enche, sai a página **menos usada recentemente** (LRU).
- Se essa página tinha sido alterada ("suja"), ela é gravada no disco antes de sair.
- `flush()` grava todas as páginas sujas. `close()` faz o flush e fecha o arquivo.

Mais detalhes em `notes/M1.md` e `notes/M2.md`.

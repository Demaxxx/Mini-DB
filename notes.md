# M1 - Página e arquivo de dados

## Tarefa 1 — escreve_pagina / le_pagina
Implementadas em `minidb.py`. Cada página tem PAGE_SIZE = 4096 bytes.
Testado escrevendo e lendo a página 0 com sucesso.

## Tarefa 2 — grava_registro / le_registro
Gravei um registro (id=42, matricula=100, 8 bytes) no slot 0 da página 2.

Cálculo do offset:
  offset = (pagina * PAGE_SIZE) + HEADER_SIZE + (slot * RECORD_SIZE)
  offset = (2 * 4096) + 16 + (0 * 8)
  offset = 8208

O registro ocupa os bytes 8208 a 8215 do arquivo.

Encerrei o processo Python após a gravação, reabri e li o registro de volta:
  valor lido: (42, 100) — confere com o valor gravado.


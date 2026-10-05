"""Pacote do MiniDB: junta o que vem do storage.py (M1) e do cache.py (M2)."""

from .storage import (
    PAGE_SIZE,
    HEADER_SIZE,
    RECORD_SIZE,
    SLOTS_POR_PAGINA,
    DiskStorage,
    Pager,
    calcula_deslocamento,
    serializa_registro,
    desserializa_registro,
    grava_registro_slot,
    le_registro_slot,
)
from .cache import BufferPool, PageCache

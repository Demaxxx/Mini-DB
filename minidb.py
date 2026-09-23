import os
import struct

# --- configurações fixas do BD ---
PAGE_SIZE = 4096    
HEADER_SIZE = 16      
RECORD_SIZE = 8       
MAGICO = 1234567890   
CAMINHO = "minidb.db"  


# ---------- ler e escrever blocos de 4096 bytes ----------

def escreve_pagina(numero_pagina, dados):
    # dados precisa ter exatamente 4096 bytes
    if len(dados) != PAGE_SIZE:
        print("ERRO: a página precisa ter", PAGE_SIZE, "bytes")
        return

    # se o arquivo não existe ainda, cria ele vazio
    if not os.path.exists(CAMINHO):
        arquivo_vazio = open(CAMINHO, "wb")
        arquivo_vazio.close()

    arquivo = open(CAMINHO, "r+b")
    arquivo.seek(numero_pagina * PAGE_SIZE)
    arquivo.write(dados)
    arquivo.close()


def le_pagina(numero_pagina):
    arquivo = open(CAMINHO, "rb")
    arquivo.seek(numero_pagina * PAGE_SIZE)
    dados = arquivo.read(PAGE_SIZE)
    arquivo.close()
    return dados


def conta_paginas():
    # quantas páginas o arquivo tem = tamanho do arquivo dividido por 4096
    if not os.path.exists(CAMINHO):
        return 0
    tamanho_arquivo = os.path.getsize(CAMINHO)
    return tamanho_arquivo // PAGE_SIZE


def cria_pagina_em_branco():
    # cria uma página nova, cheia de zeros, no fim do arquivo
    numero_nova_pagina = conta_paginas()
    pagina_zerada = bytes(PAGE_SIZE)  # 4096 bytes zerados
    escreve_pagina(numero_nova_pagina, pagina_zerada)
    return numero_nova_pagina


# ---------- CABEÇALHO DA PÁGINA (16 primeiros bytes) ----------

def monta_cabecalho(pagina_bytes, quantidade_de_registros):
    # pagina_bytes precisa ser um bytearray (lista de bytes que pode ser alterada)
    numero_em_bytes = struct.pack('<I', quantidade_de_registros)  # 4 bytes
    for i in range(len(numero_em_bytes)):
        pagina_bytes[i] = numero_em_bytes[i]
    return pagina_bytes


def le_cabecalho(pagina_bytes):
    quatro_bytes = pagina_bytes[0:4]
    (quantidade_de_registros,) = struct.unpack('<I', quatro_bytes)
    return quantidade_de_registros


# ---------- PÁGINA 0 (número mágico + tamanho da página) ----------

def cria_pagina_zero():
    pagina = bytearray(PAGE_SIZE)  # começa toda zerada
    cabecalho = struct.pack('<II', MAGICO, PAGE_SIZE)  # 8 bytes: magico + tamanho
    for i in range(len(cabecalho)):
        pagina[i] = cabecalho[i]
    escreve_pagina(0, bytes(pagina))


def confere_pagina_zero():
    pagina = le_pagina(0)
    oito_bytes = pagina[0:8]
    magico, tamanho_pagina = struct.unpack('<II', oito_bytes)

    if magico != MAGICO:
        print("ATENÇÃO: esse arquivo não parece ser um minidb válido")
    else:
        print("Número mágico confere:", magico)

    print("Tamanho de página registrado:", tamanho_pagina)


# ---------- CALCULAR ONDE UM REGISTRO FICA NO ARQUIVO ----------

def calcula_offset(numero_pagina, slot):
    return (numero_pagina * PAGE_SIZE) + HEADER_SIZE + (slot * RECORD_SIZE)


# ---------- TRANSFORMAR ALUNO EM BYTES E VICE-VERSA ----------

def serializa_aluno(id_aluno, matricula):
    return struct.pack('<II', id_aluno, matricula)


def desserializa_aluno(dados):
    id_aluno, matricula = struct.unpack('<II', dados)
    return id_aluno, matricula


# ---------- GRAVAR E LER UM REGISTRO DENTRO DE UMA PÁGINA ----------

def grava_registro(numero_pagina, slot, id_aluno, matricula):
    # 1) lê a página inteira pra memória
    pagina = bytearray(le_pagina(numero_pagina))

    # 2) transforma o aluno em bytes
    registro_em_bytes = serializa_aluno(id_aluno, matricula)

    # 3) calcula em que posição DENTRO da página o registro fica
    posicao_na_pagina = HEADER_SIZE + (slot * RECORD_SIZE)

    # 4) substitui esses 8 bytes na página
    for i in range(RECORD_SIZE):
        pagina[posicao_na_pagina + i] = registro_em_bytes[i]

    # 5) atualiza o cabeçalho dizendo que agora tem 1 registro
    monta_cabecalho(pagina, 1)

    # 6) grava a página inteira de volta no arquivo
    escreve_pagina(numero_pagina, bytes(pagina))


def le_registro(numero_pagina, slot):
    pagina = le_pagina(numero_pagina)
    posicao_na_pagina = HEADER_SIZE + (slot * RECORD_SIZE)
    registro_em_bytes = pagina[posicao_na_pagina : posicao_na_pagina + RECORD_SIZE]
    return desserializa_aluno(registro_em_bytes)


# ---------- GARANTIR QUE OS DADOS FORAM PRO DISCO DE VERDADE ----------

def sincroniza():
    # abre o arquivo só pra forçar o sistema operacional a gravar tudo no disco
    arquivo = open(CAMINHO, "r+b")
    arquivo.flush()
    os.fsync(arquivo.fileno())
    arquivo.close()


# ==================== PROGRAMA PRINCIPAL ====================

if __name__ == "__main__":

    # se o arquivo ainda não existe, cria a página 0 (com o número mágico)
    if not os.path.exists(CAMINHO):
        print("Arquivo não existia, criando página 0...")
        cria_pagina_zero()

    # garante que existem páginas suficientes até a página 2
    while conta_paginas() <= 2:
        numero = cria_pagina_em_branco()
        print("Página criada:", numero)

    # confere se a página 0 está correta
    confere_pagina_zero()

    # grava um registro de exemplo no slot 0 da página 2
    grava_registro(numero_pagina=2, slot=0, id_aluno=42, matricula=100)
    sincroniza()
    print("Registro gravado!")

    # lê o registro de volta pra confirmar
    id_lido, matricula_lida = le_registro(numero_pagina=2, slot=0)
    print("Registro lido de volta -> id_aluno:", id_lido, "| matricula:", matricula_lida)

    offset = calcula_offset(2, 0)
    print("O registro começa no byte:", offset)
    print("Total de páginas no arquivo:", conta_paginas())
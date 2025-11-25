import fitz  # PyMuPDF
import re
import os
import unicodedata

# === CONFIGURAÇÕES ===
input_pdf = "Notas.pdf"
output_dir = "faturas_separadas"
CARACTERES_COMPARACAO = 30 

os.makedirs(output_dir, exist_ok=True)

# === FUNÇÕES DE PADRONIZAÇÃO ===

def remover_acentos(texto):
    """Transforma 'JOÃO DA SILVA' em 'JOAO DA SILVA'"""
    if not texto: return ""
    nfkd = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def limpar_nome_padrao(nome):
    """
    Padronização completa: Remove acentos, caracteres especiais
    e deixa maiúsculo para garantir compatibilidade com as pastas.
    """
    if not nome:
        return "DESCONHECIDO"

    # 1. Ajustes prévios
    nome = nome.replace("&", " E ")

    # 2. Remove código do cliente no inicio se houver (ex: 010251 - NOME)
    nome = re.sub(r"^\d+\s*-\s*", "", nome)

    # 3. Remove Acentos (AQUI ESTAVA O PROBLEMA ANTES)
    nome = remover_acentos(nome)

    # 4. Tira pontos, traços, parênteses
    nome = re.sub(r'[.\(\)\-/]', " ", nome)

    # 5. Tira caracteres proibidos
    nome = re.sub(r'[\\*?:"<>|]', "", nome)

    # 6. Espaços duplos e maiúsculo
    return " ".join(nome.split()).upper()

def encontrar_pasta_destino(nome_cliente_limpo):
    """
    Procura na pasta 'faturas_separadas' se já existe uma pasta compatível
    (mesmo início de nome, ignorando sufixos).
    """
    chave_busca = nome_cliente_limpo[:CARACTERES_COMPARACAO]
    
    # Lista todas as pastas que já existem
    if os.path.exists(output_dir):
        pastas_existentes = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))]
    else:
        pastas_existentes = []
    
    for pasta in pastas_existentes:
        # Limpa o nome da pasta existente usando a MESMA REGRA para comparar
        pasta_limpa = limpar_nome_padrao(pasta)
        
        # Se o começo for igual, retorna essa pasta existente
        if pasta_limpa.startswith(chave_busca):
            return os.path.join(output_dir, pasta)
            
    # Se não achou, retorna o caminho para criar uma nova
    return os.path.join(output_dir, nome_cliente_limpo)

# === PROCESSAMENTO DO PDF ===

print("Iniciando fatiamento de notas...")

try:
    pdf = fitz.open(input_pdf)
except Exception as e:
    print(f"Erro ao abrir o arquivo {input_pdf}: {e}")
    exit()

# Regex ajustado para capturar o nome após o rótulo
regex_cliente = re.compile(r"NOME/RAZÃO SOCIAL:\s*(.+)")

notas = []
pagina_atual = 0
total_paginas = len(pdf)

while pagina_atual < total_paginas:
    texto = pdf[pagina_atual].get_text("text")
    match = regex_cliente.search(texto)

    if match:
        # 1. Captura e limpa o nome (Agora removendo acentos)
        nome_raw = match.group(1).strip()
        cliente_limpo = limpar_nome_padrao(nome_raw)
        
        inicio = pagina_atual

        # 2. Procura onde começa a próxima nota para definir o fim desta
        proxima = inicio + 1
        while proxima < total_paginas:
            texto_prox = pdf[proxima].get_text("text")
            
            # Verifica se começou uma nova nota
            if "NOME/RAZÃO SOCIAL" in texto_prox or "DESTINATÁRIO / REMETENTE" in texto_prox:
                if regex_cliente.search(texto_prox): 
                    break
            proxima += 1

        notas.append((cliente_limpo, inicio, proxima))
        pagina_atual = proxima
    else:
        pagina_atual += 1

# === SALVAMENTO ===

for cliente, inicio, fim in notas:
    # 1. Encontra a pasta correta (existente ou nova)
    pasta_destino = encontrar_pasta_destino(cliente)
    os.makedirs(pasta_destino, exist_ok=True)
    
    # 2. Cria o novo PDF apenas com as páginas daquela nota
    novo_pdf = fitz.open()
    for i in range(inicio, fim):
        novo_pdf.insert_pdf(pdf, from_page=i, to_page=i)
    
    # 3. Define nome do arquivo e evita sobrescrever
    nome_arquivo = f"Nota_{cliente}.pdf"
    caminho_final = os.path.join(pasta_destino, nome_arquivo)
    
    contador = 1
    while os.path.exists(caminho_final):
        caminho_final = os.path.join(pasta_destino, f"Nota_{cliente} ({contador}).pdf")
        contador += 1

    novo_pdf.save(caminho_final)
    novo_pdf.close()
    
    # Pega apenas o nome da pasta para o print ficar limpo
    nome_pasta = os.path.basename(pasta_destino)
    print(f"[SALVO] {nome_pasta}/{os.path.basename(caminho_final)}")

pdf.close()
print("\nSeparação e organização concluída!")
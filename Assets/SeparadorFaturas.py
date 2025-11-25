import os
import re
import unicodedata
from PyPDF2 import PdfReader, PdfWriter

# === CONFIGURAÇÕES ===
input_pdf = "faturas.pdf"
output_dir = "faturas_separadas"

# Verifica se arquivo existe
if not os.path.exists(input_pdf):
    print(f"Arquivo '{input_pdf}' nao encontrado.")
    exit()

os.makedirs(output_dir, exist_ok=True)
reader = PdfReader(input_pdf)

print("Separando faturas...")

# Variaveis de controle
paginas_buffer = []
num_fatura_anterior = None
nome_cliente_atual = "Cliente_Desconhecido"

def remover_acentos(texto):
    """Transforma 'JOÃO DA SILVA' em 'JOAO DA SILVA'"""
    if not texto: return ""
    nfkd = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def limpar_nome_pasta(nome):
    """Remove caracteres especiais, acentos e padroniza."""
    nome = nome.replace("&", " E ")

    # Remove código do cliente no inicio (ex: 010251 - NOME)
    nome = re.sub(r"^\d+\s*-\s*", "", nome)
    
    # 1. Remove Acentos
    nome = remover_acentos(nome)
    
    # 2. Troca pontos, hífens, parenteses por ESPAÇO
    nome = re.sub(r'[.\(\)\-/]', " ", nome)
    
    # 3. Remove caracteres proibidos pelo Windows/Linux
    nome = re.sub(r'[\\*?:"<>|]', "", nome)
    
    # Remove espaços duplos e deixa maiusculo
    return " ".join(nome.split()).upper()

def salvar_fatura(paginas, cliente, numero_fatura):
    if not paginas: return
    
    # Aplica a limpeza no nome (remove acentos e simbolos)
    cliente_limpo = limpar_nome_pasta(cliente)
    
    # Cria pasta
    pasta_cliente = os.path.join(output_dir, cliente_limpo)
    os.makedirs(pasta_cliente, exist_ok=True)
    
    # Salva o arquivo
    caminho_arquivo = os.path.join(pasta_cliente, f"{cliente_limpo}_Fatura_{numero_fatura}.pdf")
    
    writer = PdfWriter()
    for p in paginas:
        writer.add_page(p)
        
    with open(caminho_arquivo, "wb") as f:
        writer.write(f)
    print(f"Salvo: {caminho_arquivo}")

# Loop principal
for i, page in enumerate(reader.pages):
    text = page.extract_text()

    # Busca numero da fatura
    match_fatura = re.search(r"Fatura nr\.?:?\s*(\d+)", text, re.IGNORECASE)
    # Busca nome do cliente
    match_cliente = re.search(r"Cliente\.\:\s*(.+)", text)
    
    num_fatura_atual = match_fatura.group(1) if match_fatura else f"sem_numero_{i}"
    cliente_lido = match_cliente.group(1).strip() if match_cliente else None

    # Lógica de quebra de fatura
    if num_fatura_anterior and num_fatura_atual != num_fatura_anterior:
        salvar_fatura(paginas_buffer, nome_cliente_atual, num_fatura_anterior)
        paginas_buffer = [] 

    paginas_buffer.append(page)
    num_fatura_anterior = num_fatura_atual
    if cliente_lido:
        nome_cliente_atual = cliente_lido

# Salva a última
salvar_fatura(paginas_buffer, nome_cliente_atual, num_fatura_anterior)

print("\nFaturas separadas com nomes limpos e sem acentos!")
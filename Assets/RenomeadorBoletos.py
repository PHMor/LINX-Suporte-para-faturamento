import os
import re
from PyPDF2 import PdfReader

# === CONFIGURAÇÕES ===
input_dir = "boletos"
output_dir = "faturas_separadas"
CARACTERES_COMPARACAO = 30  # Compara apenas os primeiros 30 letras para ignorar o corte

if not os.path.exists(input_dir):
    print(f"A pasta de entrada '{input_dir}' não existe.")
    exit()

os.makedirs(output_dir, exist_ok=True)

def limpar_nome_padrao(nome):
    """Mesma lógica de limpeza do separador de faturas para garantir compatibilidade"""
    nome = re.sub(r'[.\(\)\-/]', " ", nome) # Tira pontos, tracos, parenteses
    nome = re.sub(r'[\\*?:"<>|]', "", nome) # Tira proibidos
    return " ".join(nome.split()).upper()   # Tira espacos duplos e deixa maiusculo

def encontrar_pasta_destino(nome_boleto_limpo):
    """
    Procura na pasta de destino se existe alguma pasta que comece
    com os mesmos caracteres do nome do boleto.
    """
    chave_busca = nome_boleto_limpo[:CARACTERES_COMPARACAO]
    
    # Lista todas as pastas que já existem (criadas pelas faturas)
    pastas_existentes = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))]
    
    for pasta in pastas_existentes:
        # Limpa o nome da pasta também para comparar de igual para igual
        pasta_limpa = limpar_nome_padrao(pasta)
        
        # Se o começo for igual, achamos a pasta correta!
        if pasta_limpa.startswith(chave_busca):
            return os.path.join(output_dir, pasta)
            
    # Se não achou nenhuma parecida, retorna o caminho para criar uma nova com o nome do boleto
    return os.path.join(output_dir, nome_boleto_limpo)

print(f"Processando boletos...\n")

for arquivo in os.listdir(input_dir):
    if not arquivo.lower().endswith(".pdf"):
        continue

    caminho_antigo = os.path.join(input_dir, arquivo)

    try:
        leitor = PdfReader(caminho_antigo)
        texto = ""
        for pagina in leitor.pages:
            texto += pagina.extract_text()

        # Busca nome (Multilinha)
        match = re.search(r"Nome do Pagador:\s*(.+?)\s*(?:CPF|CNPJ|Endereço|$)", texto, re.IGNORECASE | re.DOTALL)
        
        if not match:
            print(f"[PULADO] Não encontrei pagador em: {arquivo}")
            continue

        # 1. Limpa o nome do boleto
        nome_raw = match.group(1).replace("\n", " ").strip()
        nome_limpo = limpar_nome_padrao(nome_raw)
        
        # 2. Encontra a pasta correta (ou define a nova)
        pasta_destino = encontrar_pasta_destino(nome_limpo)
        os.makedirs(pasta_destino, exist_ok=True)

        # 3. Define nome do arquivo
        novo_nome_arquivo = f"{nome_limpo}.pdf"
        caminho_novo = os.path.join(pasta_destino, novo_nome_arquivo)

        # 4. Evita sobrescrever
        i = 1
        while os.path.exists(caminho_novo):
            caminho_novo = os.path.join(pasta_destino, f"{nome_limpo} ({i}).pdf")
            i += 1

        # 5. Move
        os.rename(caminho_antigo, caminho_novo)
        nome_pasta_final = os.path.basename(pasta_destino)
        print(f"[SUCESSO] {arquivo} -> {nome_pasta_final}/{os.path.basename(caminho_novo)}")

    except Exception as e:
        print(f"[ERRO] Falha ao processar {arquivo}: {e}")

print("\nOrganização concluída!")
import os
from PIL import Image

# === CONFIGURAÇÕES ===
output_dir = "faturas_separadas"
assinaturas_dir = "Assinaturas"

# === 2. Criar PDFs de assinaturas por cliente ===
print("Gerando PDFs de assinaturas...")

if os.path.exists(assinaturas_dir):
    # Dicionário para agrupar imagens por cliente
    imagens_por_cliente = {}

    for arquivo in os.listdir(assinaturas_dir):
        caminho_arquivo = os.path.join(assinaturas_dir, arquivo)

        if os.path.isfile(caminho_arquivo):
            partes = arquivo.split("_", 1)
            if len(partes) == 2:
                nome_cliente = partes[1].split(".")[0].replace("_", " ").strip()

                if nome_cliente not in imagens_por_cliente:
                    imagens_por_cliente[nome_cliente] = []
                imagens_por_cliente[nome_cliente].append(caminho_arquivo)

    # Gerar 1 PDF por cliente
    for cliente, lista_imagens in imagens_por_cliente.items():
        pasta_cliente = os.path.join(output_dir, cliente)

        #  Se a pasta não existir, cria automaticamente
        os.makedirs(pasta_cliente, exist_ok=True)

        # Ordenar lista para manter consistência (por nome)
        lista_imagens.sort()

        imagens_convertidas = []
        for img_path in lista_imagens:
            try:
                img = Image.open(img_path).convert("RGB")
                imagens_convertidas.append(img)
            except Exception as e:
                print(f"Erro ao abrir imagem {img_path}: {e}")

        if imagens_convertidas:
            output_pdf = os.path.join(pasta_cliente, f"Assinaturas_{cliente}.pdf")
            primeira = imagens_convertidas[0]
            restantes = imagens_convertidas[1:]
            primeira.save(output_pdf, save_all=True, append_images=restantes)
            print(f"PDF de assinaturas criado para {cliente}: {output_pdf}")
        else:
            print(f"Nenhuma imagem válida encontrada para {cliente}")

else:
    print("Pasta 'Assinaturas' não encontrada.")

print("\nProcesso de assinaturas concluído com sucesso!")

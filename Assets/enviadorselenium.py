import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# === CONFIGURAÇÕES GERAIS ===
USER_DATA_DIR = os.path.join(os.getcwd(), 'Assets')
PASTA_CLIENTES = "faturas_separadas"  # pasta com subpastas dos clientes
ARQUIVO_EXCEL = "Assets/clientes.xlsx"       # planilha com Nome e Telefone
ARQUIVO_MENSAGEM = "Assets/mensagem.txt"

try:
    with open(ARQUIVO_MENSAGEM, "r", encoding="utf-8") as f:
        MENSAGEM_PADRAO = f.read()
except Exception as e:
    print(f"Erro ao ler mensagem.txt: {e}")
    MENSAGEM_PADRAO = "Bom dia, segue sua fatura."

# === CONFIGURAÇÃO DO CHROME / SELENIUM ===
options = Options()
options.add_argument(f"user-data-dir={USER_DATA_DIR}")
options.add_argument("--start-maximized")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--user-data-dir=C:/Selenium/ChromeProfile")  # mantém login
options.add_argument("--profile-directory=Default")

servico = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=servico, options=options)
wait = WebDriverWait(driver, 30)

# === INICIAR WHATSAPP WEB ===
print("Abrindo o WhatsApp Web...")
driver.get("https://web.whatsapp.com")

print("Escaneie o QR Code (se necessário) e pressione ENTER para continuar...", flush=True)
input()

# === LER PLANILHA ===
tabela = pd.read_excel(ARQUIVO_EXCEL, dtype={"Telefone": str})

# Criar dicionário nome -> telefone (ignora valores vazios)
mapa_telefones = {}
for _, linha in tabela.iterrows():
    nome = str(linha.get("Nome", "")).strip()
    telefone = str(linha.get("Telefone", "")).strip()
    if nome and telefone and telefone.lower() != "nan":
        mapa_telefones[nome.lower()] = telefone

# === PEGAR CLIENTES COM PASTA ===
clientes_com_pasta = [
    nome for nome in os.listdir(PASTA_CLIENTES)
    if os.path.isdir(os.path.join(PASTA_CLIENTES, nome)) and not nome.endswith("(enviado)")
]

nao_enviados = []  # lista para registrar falhas

# === LOOP PARA CADA CLIENTE COM PASTA ===
for nome_cliente in sorted(clientes_com_pasta):
    nome_chave = nome_cliente.lower()
    telefone = mapa_telefones.get(nome_chave)

    if not telefone or telefone.lower() == "nan" or telefone.strip() == "":
        print(f" {nome_cliente} não possui telefone na planilha.")
        nao_enviados.append(nome_cliente)
        continue

    mensagem = MENSAGEM_PADRAO.format(nome=nome_cliente)
    print(f"\n Enviando para {nome_cliente} ({telefone})...")

    # Abre conversa
    link = f"https://web.whatsapp.com/send?phone={telefone}&text={mensagem}"
    driver.get(link)

    try:
        # Campo de texto da mensagem
        campo_mensagem = wait.until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
        )
        campo_mensagem.send_keys(Keys.ENTER)
        print(" Mensagem enviada.")
    except Exception as e:
        print(f" Erro ao enviar mensagem para {nome_cliente}: {e}")
        nao_enviados.append(nome_cliente)
        continue

    # === ENVIAR ARQUIVOS DO CLIENTE ===
    pasta_cliente = os.path.join(PASTA_CLIENTES, nome_cliente)
    arquivos = [
        os.path.abspath(os.path.join(pasta_cliente, a))
        for a in os.listdir(pasta_cliente)
        if a.lower().endswith((".pdf", ".jpg", ".jpeg", ".png"))
    ]

    if not arquivos:
        print(" Nenhum arquivo para enviar.")
        continue

    print(f" Encontrados {len(arquivos)} arquivos para enviar...")

    try:
        botao_plus = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span[data-icon='plus-rounded']"))
        )
        botao_plus.click()
        time.sleep(1)

        input_arquivo = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
        )
        input_arquivo.send_keys("\n".join(arquivos))

        botao_enviar = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span[data-icon='wds-ic-send-filled']"))
        )
        driver.execute_script("arguments[0].click();", botao_enviar)

        print(" Arquivos enviados com sucesso.")
        os.rename(pasta_cliente, os.path.join(PASTA_CLIENTES, f"{nome_cliente} (enviado)"))
        time.sleep(5)

    except Exception as e:
        print(f" Erro ao enviar arquivos para {nome_cliente}: {e}")
        nao_enviados.append(nome_cliente)

# === RELATÓRIO FINAL ===
print("\n Processo concluído.")
if nao_enviados:
    print("\n Clientes que **não** receberam mensagem:")
    for nome in nao_enviados:
        print(" -", nome)
else:
    print("\n Todos os clientes receberam mensagem com sucesso.")

driver.quit()

import os
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

# === CONFIGURACOES ===
PASTA_INTERNA_BOLETOS = "boletos"
PASTA_INTERNA_ASSINATURAS = "Assinaturas"

# Nomes internos padronizados para os arquivos que os scripts vão ler
ARQUIVO_INTERNO_FATURAS = "faturas.pdf"
ARQUIVO_INTERNO_NOTAS = "Notas.pdf" 
ARQUIVO_MENSAGEM = "Assets/mensagem.txt"

# Caminhos dos scripts (Certifique-se que o FatiadorNotas.py está na pasta Assets)
SCRIPT_FATURAS = "Assets/SeparadorFaturas.py"
SCRIPT_ASSINATURAS = "Assets/SeparadorAssinaturas.py"
SCRIPT_BOLETOS = "Assets/RenomeadorBoletos.py"
SCRIPT_NOTAS = "Assets/FatiadorNotas.py"
SCRIPT_WHATSAPP = "Assets/enviadorselenium.py"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerenciador de Faturas Automático")
        self.geometry("650x850") # Aumentei um pouco a altura para caber os novos botões
        self.configure(bg="#f0f0f0")

        self.processo_atual = None

        os.makedirs(PASTA_INTERNA_BOLETOS, exist_ok=True)
        os.makedirs(PASTA_INTERNA_ASSINATURAS, exist_ok=True)

        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # === SEÇÃO 1: ENTRADAS ===
        frame_inputs = ttk.LabelFrame(self, text="1. Carregar Arquivos", padding=10)
        frame_inputs.pack(fill="x", padx=10, pady=5)

        self.cria_seletor_arquivo(frame_inputs, "PDF Completo (Faturas):", self.carregar_faturas)
        self.cria_seletor_arquivo(frame_inputs, "PDF de Notas:", self.carregar_notas) # NOVO
        self.cria_seletor_pasta(frame_inputs, "Pasta dos Boletos:", self.carregar_boletos)
        self.cria_seletor_pasta(frame_inputs, "Pasta das Assinaturas:", self.carregar_assinaturas)

        # === SEÇÃO 2: AÇÕES ===
        frame_acoes = ttk.LabelFrame(self, text="2. Executar Tarefas", padding=10)
        frame_acoes.pack(fill="x", padx=10, pady=5)

        ttk.Button(frame_acoes, text="Separar Faturas (PDF Geral)", command=lambda: self.rodar_script(SCRIPT_FATURAS)).pack(fill="x", pady=2)
        ttk.Button(frame_acoes, text="Separar Notas Fiscais", command=lambda: self.rodar_script(SCRIPT_NOTAS)).pack(fill="x", pady=2) # NOVO
        ttk.Button(frame_acoes, text="Organizar Assinaturas", command=lambda: self.rodar_script(SCRIPT_ASSINATURAS)).pack(fill="x", pady=2)
        ttk.Button(frame_acoes, text="Renomear Boletos", command=lambda: self.rodar_script(SCRIPT_BOLETOS)).pack(fill="x", pady=2)
        
        ttk.Separator(frame_acoes, orient='horizontal').pack(fill='x', pady=8)

        # Botão de editar mensagem
        ttk.Button(frame_acoes, text="📝 Editar Mensagem Padrão", command=self.abrir_editor_mensagem).pack(fill="x", pady=2)
        
        btn_whats = tk.Button(frame_acoes, text="ENVIAR TUDO NO WHATSAPP", bg="#008080", fg="white", font=("Arial", 10, "bold"), command=lambda: self.rodar_script(SCRIPT_WHATSAPP))
        btn_whats.pack(fill="x", pady=2)

        # === SEÇÃO 3: CONTROLES ===
        frame_controles = ttk.LabelFrame(self, text="Controles de Execução", padding=10)
        frame_controles.pack(fill="x", padx=10, pady=5)

        coluna_botoes = ttk.Frame(frame_controles)
        coluna_botoes.pack(fill="x")

        self.btn_confirmar = tk.Button(coluna_botoes, text="Aguardando solicitação...", bg="#cccccc", fg="#666666", state="disabled", command=self.enviar_enter)
        self.btn_confirmar.pack(side="left", fill="x", expand=True, padx=2)

        self.btn_parar = tk.Button(coluna_botoes, text="🛑 PARAR TUDO", bg="#FF5252", fg="white", state="disabled", command=self.parar_processo)
        self.btn_parar.pack(side="right", fill="x", expand=True, padx=2)

        # === SEÇÃO 4: LOGS ===
        frame_log = ttk.LabelFrame(self, text="Status e Logs", padding=10)
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.text_log = scrolledtext.ScrolledText(frame_log, height=10, state='disabled', bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9))
        self.text_log.pack(fill="both", expand=True)

    # --- NOVA FUNÇÃO: EDITOR DE MENSAGEM ---
    def abrir_editor_mensagem(self):
        janela_edit = tk.Toplevel(self)
        janela_edit.title("Editar Mensagem do WhatsApp")
        janela_edit.geometry("500x400")

        lbl_info = ttk.Label(janela_edit, text="Edite abaixo. Use {nome} onde quiser que apareça o nome do cliente.", wraplength=480)
        lbl_info.pack(pady=5)

        txt_msg = scrolledtext.ScrolledText(janela_edit, width=60, height=15)
        txt_msg.pack(padx=10, pady=5, fill="both", expand=True)

        # Carrega msg atual
        if os.path.exists(ARQUIVO_MENSAGEM):
            with open(ARQUIVO_MENSAGEM, "r", encoding="utf-8") as f:
                txt_msg.insert("1.0", f.read())

        def salvar_msg():
            conteudo = txt_msg.get("1.0", tk.END).strip()
            try:
                with open(ARQUIVO_MENSAGEM, "w", encoding="utf-8") as f:
                    f.write(conteudo)
                messagebox.showinfo("Sucesso", "Mensagem salva com sucesso!")
                janela_edit.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar: {e}")

        ttk.Button(janela_edit, text="Salvar Alteração", command=salvar_msg).pack(pady=10, fill="x", padx=20)

    # --- FUNÇÕES DE INTERFACE ---
    def cria_seletor_arquivo(self, parent, label_text, comando):
        container = ttk.Frame(parent)
        container.pack(fill="x", pady=3)
        ttk.Label(container, text=label_text, width=25, anchor="w").pack(side="left")
        ttk.Button(container, text="Selecionar Arquivo...", command=comando).pack(side="right", fill="x", expand=True)

    def cria_seletor_pasta(self, parent, label_text, comando):
        container = ttk.Frame(parent)
        container.pack(fill="x", pady=3)
        ttk.Label(container, text=label_text, width=25, anchor="w").pack(side="left")
        ttk.Button(container, text="Selecionar Pasta...", command=comando).pack(side="right", fill="x", expand=True)

    def log(self, mensagem):
        self.text_log.configure(state='normal')
        self.text_log.insert(tk.END, f">> {mensagem}\n")
        self.text_log.see(tk.END)
        self.text_log.configure(state='disabled')

    def estado_botoes(self, rodando, confirmacao_pendente=False):
        if not rodando:
            self.btn_parar.config(state="disabled", bg="#FF5252")
            self.btn_confirmar.config(state="disabled", text="Aguardando solicitação...", bg="#cccccc", fg="#666666")
        else:
            self.btn_parar.config(state="normal")
            if confirmacao_pendente:
                self.btn_confirmar.config(state="normal", text="✅ JÁ ESCANEEI (CONTINUAR)", bg="#4CAF50", fg="white")
            else:
                self.btn_confirmar.config(state="disabled", text="Rodando... Aguarde", bg="#cccccc", fg="#666666")

    # --- FUNÇÕES LÓGICAS ---
    def carregar_faturas(self):
        caminho = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if caminho:
            try:
                shutil.copy(caminho, ARQUIVO_INTERNO_FATURAS)
                self.log(f"OK: Faturas carregadas para {ARQUIVO_INTERNO_FATURAS}.")
            except Exception as e:
                self.log(f"ERRO: {e}")

    # NOVA FUNÇÃO PARA CARREGAR AS NOTAS
    def carregar_notas(self):
        caminho = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if caminho:
            try:
                shutil.copy(caminho, ARQUIVO_INTERNO_NOTAS)
                self.log(f"OK: Notas carregadas para {ARQUIVO_INTERNO_NOTAS}.")
            except Exception as e:
                self.log(f"ERRO: {e}")

    def carregar_pasta_generica(self, nome_pasta_destino, titulo_acao):
        caminho_origem = filedialog.askdirectory()
        if not caminho_origem: return
        self.log(f"Importando {titulo_acao}...")
        try:
            for f in os.listdir(nome_pasta_destino):
                fp = os.path.join(nome_pasta_destino, f)
                if os.path.isfile(fp): os.remove(fp)
            
            copiados = 0
            for f in os.listdir(caminho_origem):
                src = os.path.join(caminho_origem, f)
                dst = os.path.join(nome_pasta_destino, f)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                    copiados += 1
            self.log(f"OK: {copiados} arquivos importados.")
        except Exception as e:
            self.log(f"ERRO: {e}")

    def carregar_boletos(self):
        self.carregar_pasta_generica(PASTA_INTERNA_BOLETOS, "Boletos")

    def carregar_assinaturas(self):
        self.carregar_pasta_generica(PASTA_INTERNA_ASSINATURAS, "Assinaturas")

    # --- CONTROLE DE PROCESSOS ---
    def enviar_enter(self):
        if self.processo_atual and self.processo_atual.poll() is None:
            try:
                self.processo_atual.stdin.write("\n")
                self.processo_atual.stdin.flush()
                self.log(">> [CONFIRMAÇÃO ENVIADA]")
                self.estado_botoes(rodando=True, confirmacao_pendente=False)
            except Exception as e:
                self.log(f"Erro ao enviar confirmação: {e}")

    def parar_processo(self):
        if self.processo_atual and self.processo_atual.poll() is None:
            try:
                self.processo_atual.kill()
                self.log(">> [INTERROMPIDO] Processo parado pelo usuário.")
                self.processo_atual = None
                self.estado_botoes(rodando=False)
            except Exception as e:
                self.log(f"Erro ao parar: {e}")

    def rodar_script(self, script_path):
        if self.processo_atual and self.processo_atual.poll() is None:
            self.log(" Já existe um processo rodando.")
            return

        if not os.path.exists(script_path):
            self.log(f"ERRO: Script não encontrado: {script_path}")
            return

        self.estado_botoes(rodando=True, confirmacao_pendente=False)

        def thread_target():
            self.log(f"--- INICIANDO: {os.path.basename(script_path)} ---")
            try:
                self.processo_atual = subprocess.Popen(
                    ["python", "-u",script_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    encoding='utf-8', 
                    errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                for line in self.processo_atual.stdout:
                    texto = line.strip()
                    self.log(texto)
                    
                    if "Escaneie o QR Code" in texto:
                        self.after(0, lambda: self.estado_botoes(rodando=True, confirmacao_pendente=True))

                self.processo_atual.wait()
                
                if self.processo_atual.returncode == 0:
                    self.log(f"--- SUCESSO ---")
                elif self.processo_atual.returncode != -9: 
                    self.log(f"--- ERRO/FINALIZADO (Código {self.processo_atual.returncode}) ---")
                    erro = self.processo_atual.stderr.read()
                    if erro: self.log(f"Log de Erro: {erro}")

            except Exception as e:
                self.log(f"Erro de execução: {e}")
            finally:
                self.processo_atual = None
                self.after(0, lambda: self.estado_botoes(rodando=False))

        threading.Thread(target=thread_target, daemon=True).start()

if __name__ == "__main__":
    app = App()
    app.mainloop()
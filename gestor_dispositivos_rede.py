import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, filedialog
import json, os

MARCAS_PREDEFINIDAS = ["Cisco", "Palo Alto", "Huawei", "Juniper", "Dell", "HP", "Arista", "Fortinet", "Check Point", "Outra"]
script_dir = os.path.dirname(os.path.realpath(__file__))
FICHEIRO_AUTOLOAD = os.path.join(script_dir, "dispositivos.txt")

class DispositivoRede:
    def __init__(self, nome, marca, modelo):
        self.nome = nome; self.marca = marca; self.modelo = modelo
        self.estado = "Desligado"
    def ligar(self): self.estado = "Ligado"
    def desligar(self): self.estado = "Desligado"
    def mostrar_info(self):
        return {"Nome": self.nome, "Marca": self.marca, "Modelo": self.modelo,
                "Estado": self.estado, "Tipo": self.__class__.__name__}
    def to_dict(self):
        info = self.mostrar_info()
        info['dados_especificos'] = self.get_dados_especificos()
        return info
    def get_dados_especificos(self): return {}
    def get_ip_principal(self): return "N/A"
    def get_ligacoes_str(self): return "N/A"

class Router(DispositivoRede):
    def __init__(self, nome, marca, modelo, num_portas):
        super().__init__(nome, marca, modelo)
        self.num_portas = num_portas
        self.interfaces_ip = []
    def get_dados_especificos(self):
        return {"num_portas": self.num_portas, "interfaces_ip": self.interfaces_ip}
    def get_ip_principal(self):
        return self.interfaces_ip[0].get("ip", "Nenhum IP") if self.interfaces_ip else "Nenhum IP"
    def get_ligacoes_str(self):
        ligacoes = [f"{item.get('iface', '?')}: {item.get('ligado_a')}" for item in self.interfaces_ip if item.get("ligado_a")]
        return ", ".join(ligacoes) if ligacoes else "Nenhuma"

class Switch(DispositivoRede):
    def __init__(self, nome, marca, modelo, num_portas, ip_gestao=""):
        super().__init__(nome, marca, modelo)
        self.num_portas = num_portas; self.ip_gestao = ip_gestao
        self.port_vlan_map = []
    def get_dados_especificos(self):
        return {"num_portas": self.num_portas, "ip_gestao": self.ip_gestao, "port_vlan_map": self.port_vlan_map}
    def get_ip_principal(self):
        return self.ip_gestao if self.ip_gestao else "N/A"
    def get_ligacoes_str(self):
        ligacoes = [f"{item.get('porta', '?')}: {item.get('ligado_a')}" for item in self.port_vlan_map if item.get("ligado_a")]
        return ", ".join(ligacoes) if ligacoes else "Nenhuma"

class Servidor(DispositivoRede):
    def __init__(self, nome, marca, modelo, endereco_ip, sistema_operativo=""):
        super().__init__(nome, marca, modelo)
        self.endereco_ip = endereco_ip; self.sistema_operativo = sistema_operativo
        self.servicos = []
    def get_dados_especificos(self):
        return {"endereco_ip": self.endereco_ip, "sistema_operativo": self.sistema_operativo, "servicos": self.servicos}
    def get_ip_principal(self):
        return self.endereco_ip

class SubFormularioMultiplo(ttk.Frame):
    def __init__(self, parent, label, labels_entrada, colunas_tree, num_required_fields=None):
        super().__init__(parent)
        self.lista_dados = []
        self.entries = []
        
        self.num_required = num_required_fields if num_required_fields is not None else len(labels_entrada)

        form_frame = ttk.LabelFrame(self, text=label)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        entry_frame = ttk.Frame(form_frame)
        entry_frame.pack(fill=tk.X, pady=5)
        num_labels = len(labels_entrada)
        has_optional_fields = num_labels > self.num_required

        for i, texto_label in enumerate(labels_entrada):
            ttk.Label(entry_frame, text=texto_label).pack(side=tk.LEFT, padx=(10, 2))
            is_required = (i < self.num_required)
            
            if has_optional_fields:
                if is_required:
                    entry = ttk.Entry(entry_frame, width=12)
                    entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.NONE, expand=False)
                else:
                    entry = ttk.Entry(entry_frame) 
                    entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True) 
            else:
                entry = ttk.Entry(entry_frame, width=15)
                entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
            self.entries.append(entry)

        
        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Adicionar Novo", command=self.adicionar_novo_item).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="Guardar Edição", command=self.guardar_edicao_selecionada).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Remover Selecionado", command=self.remover_item_selecionado).pack(side=tk.LEFT, padx=5)


        col_ids = [col[0] for col in colunas_tree]
        self.tree = ttk.Treeview(form_frame, columns=col_ids, show="headings", height=8)
        for col_id, col_text, col_width in colunas_tree:
            self.tree.heading(col_id, text=col_text)
            self.tree.column(col_id, width=col_width)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self._on_item_select)

    def _limpar_entries(self):
        for entry in self.entries:
            entry.delete(0, tk.END)

    def _on_item_select(self, event=None):
        try:

            selected_item = self.tree.selection()[0]

            valores = self.tree.item(selected_item, 'values')
            
            for entry, value in zip(self.entries, valores):
                entry.delete(0, tk.END)
                entry.insert(0, value)
        except IndexError:
            pass 

    def adicionar_novo_item(self):
        valores = [entry.get() for entry in self.entries]
        valores_requeridos = valores[:self.num_required]
        if not all(valores_requeridos):
            messagebox.showwarning("Campos Vazios", f"Preencha pelo menos os primeiros {self.num_required} campos.", parent=self)
            return
        col_ids = self.tree.cget("columns")
        dados_dict = dict(zip(col_ids, valores))
        
        self.lista_dados.append(dados_dict)
        self.tree.insert("", tk.END, values=valores)
        self._limpar_entries() 

        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def guardar_edicao_selecionada(self):
        try:

            selected_item = self.tree.selection()[0]
            index = self.tree.index(selected_item)
        except IndexError:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, clique num item da lista para o poder editar.", parent=self)
            return


        novos_valores = [entry.get() for entry in self.entries]
        

        valores_requeridos = novos_valores[:self.num_required]
        if not all(valores_requeridos):
            messagebox.showwarning("Campos Vazios", f"Os primeiros {self.num_required} campos não podem estar vazios.", parent=self)
            return


        self.tree.item(selected_item, values=novos_valores)
        

        col_ids = self.tree.cget("columns")
        dados_dict = dict(zip(col_ids, novos_valores))
        self.lista_dados[index] = dados_dict
        

        self._limpar_entries()
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def remover_item_selecionado(self):

        try:
            selected_item = self.tree.selection()[0]
            index = self.tree.index(selected_item)
            self.lista_dados.pop(index)
            self.tree.delete(selected_item)
            self._limpar_entries()
            
        except IndexError:
            messagebox.showwarning("Nenhuma Seleção", "Selecione um item da lista para remover.", parent=self)
            
    def preencher_dados(self, dados_lista):
        self.lista_dados = list(dados_lista) 
        col_ids = self.tree.cget("columns")
        for item_dict in self.lista_dados:
            valores = [item_dict.get(col_id, "") for col_id in col_ids]
            self.tree.insert("", tk.END, values=valores)

    def get_dados(self):
        return self.lista_dados

class JanelaDispositivo(Toplevel):
    def __init__(self, parent, app_controller, dispositivo=None, index=None):
        super().__init__(parent)
        self.transient(parent); self.grab_set() 
        self.app = app_controller; self.dispositivo = dispositivo; self.index = index 
        self.title("Editar Dispositivo" if self.dispositivo else "Adicionar Dispositivo")
        self.window_width = 600; self.window_height = 700
        self.geometry(f"{self.window_width}x{self.window_height}")
        self.resizable(False, False)
        self.tipo_var = tk.StringVar(); self.nome_var = tk.StringVar()
        self.marca_var = tk.StringVar(); self.modelo_var = tk.StringVar()
        self.sub_form_router = self.sub_form_switch = self.sub_form_servidor = None
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        self._criar_campos_comuns(main_frame)
        self.dynamic_frame = ttk.LabelFrame(main_frame, text="Detalhes Específicos")
        self.dynamic_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._criar_botoes(main_frame)
        self.tipo_var.trace("w", self.atualizar_campos_dinamicos)
        if self.dispositivo: self.preencher_formulario()
        else: self.tipo_combo.current(0)
        self.center_window()
    def center_window(self):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth(); screen_height = self.winfo_screenheight()
        pos_x = (screen_width // 2) - (self.window_width // 2)
        pos_y = (screen_height // 2) - (self.window_height // 2)
        self.geometry(f"+{pos_x}+{pos_y}")
    def _criar_campos_comuns(self, parent):
        common_frame = ttk.LabelFrame(parent, text="Informação Comum")
        common_frame.pack(fill=tk.X, padx=5, pady=5)
        campos = [("Tipo:", self.tipo_var), ("Nome (Hostname):", self.nome_var), ("Marca:", self.marca_var), ("Modelo:", self.modelo_var)]
        for i, (label_text, var) in enumerate(campos):
            ttk.Label(common_frame, text=label_text).grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
            if label_text == "Tipo:":
                self.tipo_combo = ttk.Combobox(common_frame, textvariable=var, values=["Router", "Switch", "Servidor"])
                self.tipo_combo.grid(row=i, column=1, padx=5, pady=5, sticky=tk.EW)
            elif label_text == "Marca:":
                self.marca_combo = ttk.Combobox(common_frame, textvariable=var, values=MARCAS_PREDEFINIDAS)
                self.marca_combo.grid(row=i, column=1, padx=5, pady=5, sticky=tk.EW)
            else:
                ttk.Entry(common_frame, textvariable=var).grid(row=i, column=1, padx=5, pady=5, sticky=tk.EW)
        common_frame.columnconfigure(1, weight=1)
    def _criar_botoes(self, parent):
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
        ttk.Button(btn_frame, text="Guardar", command=self.on_save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT, padx=5)
    def atualizar_campos_dinamicos(self, *args):
        for widget in self.dynamic_frame.winfo_children(): widget.destroy()
        self.sub_form_router = self.sub_form_switch = self.sub_form_servidor = None
        tipo = self.tipo_var.get()
        self.num_portas_var = tk.StringVar(); self.ip_gestao_var = tk.StringVar()
        self.endereco_ip_var = tk.StringVar(); self.os_var = tk.StringVar()
        if tipo == "Router":
            frame_portas = ttk.Frame(self.dynamic_frame)
            frame_portas.pack(fill=tk.X, pady=5, padx=5)
            ttk.Label(frame_portas, text="Num. Portas:").pack(side=tk.LEFT, padx=5)
            ttk.Entry(frame_portas, textvariable=self.num_portas_var, width=10).pack(side=tk.LEFT, padx=5)
            self.sub_form_router = SubFormularioMultiplo(self.dynamic_frame, "Gestão de Interfaces IP",
                labels_entrada=["Interface:", "IP:", "Máscara:", "Ligado a:"],
                colunas_tree=[("iface", "Interface", 80), ("ip", "Endereço IP", 120), ("mask", "Máscara", 120), ("ligado_a", "Onde está ligado", 120)],
                num_required_fields=3)
            self.sub_form_router.pack(fill=tk.BOTH, expand=True)
        elif tipo == "Switch":
            frame_switch = ttk.Frame(self.dynamic_frame)
            frame_switch.pack(fill=tk.X, padx=5, pady=5)
            ttk.Label(frame_switch, text="Num. Portas:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
            ttk.Entry(frame_switch, textvariable=self.num_portas_var, width=10).grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
            ttk.Label(frame_switch, text="IP Gestão:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
            ttk.Entry(frame_switch, textvariable=self.ip_gestao_var).grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
            frame_switch.columnconfigure(1, weight=1)
            self.sub_form_switch = SubFormularioMultiplo(self.dynamic_frame, "Gestão de VLANs por Porta",
                labels_entrada=["Porta:", "VLAN ID:", "Ligado a:"],
                colunas_tree=[("porta", "Porta", 100), ("vlan", "VLAN ID", 100), ("ligado_a", "Onde está ligado", 120)],
                num_required_fields=2)
            self.sub_form_switch.pack(fill=tk.BOTH, expand=True)
        elif tipo == "Servidor":
            frame_server = ttk.Frame(self.dynamic_frame)
            frame_server.pack(fill=tk.X, pady=5, padx=5)
            ttk.Label(frame_server, text="IP Principal:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
            ttk.Entry(frame_server, textvariable=self.endereco_ip_var).grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
            ttk.Label(frame_server, text="Sistema Op.:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
            ttk.Entry(frame_server, textvariable=self.os_var).grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
            frame_server.columnconfigure(1, weight=1)
            self.sub_form_servidor = SubFormularioMultiplo(self.dynamic_frame, "Gestão de Serviços",
                labels_entrada=["Serviço:", "IP Alocado:", "Placa Rede:"],
                colunas_tree=[("nome", "Serviço", 100), ("ip", "IP Alocado", 120), ("placa", "Placa Rede", 100)],
                num_required_fields=3)
            self.sub_form_servidor.pack(fill=tk.BOTH, expand=True)
    def preencher_formulario(self):
        self.nome_var.set(self.dispositivo.nome); self.marca_var.set(self.dispositivo.marca); self.modelo_var.set(self.dispositivo.modelo)
        tipo = self.dispositivo.__class__.__name__
        self.tipo_var.set(tipo); self.tipo_combo.config(state="disabled") 
        if tipo == "Router":
            self.num_portas_var.set(self.dispositivo.num_portas)
            self.sub_form_router.preencher_dados(self.dispositivo.interfaces_ip)
        elif tipo == "Switch":
            self.num_portas_var.set(self.dispositivo.num_portas)
            self.ip_gestao_var.set(self.dispositivo.ip_gestao)
            self.sub_form_switch.preencher_dados(self.dispositivo.port_vlan_map)
        elif tipo == "Servidor":
            self.endereco_ip_var.set(self.dispositivo.endereco_ip)
            self.os_var.set(self.dispositivo.sistema_operativo)
            self.sub_form_servidor.preencher_dados(self.dispositivo.servicos)
    def on_save(self):
        try:
            tipo = self.tipo_var.get(); nome = self.nome_var.get(); marca = self.marca_var.get(); modelo = self.modelo_var.get()
            if not all([tipo, nome, marca, modelo]): raise ValueError("Preencha todos os campos comuns.")
            novo_dispositivo = None
            if tipo == "Router":
                novo_dispositivo = Router(nome, marca, modelo, int(self.num_portas_var.get()))
                novo_dispositivo.interfaces_ip = self.sub_form_router.get_dados()
            elif tipo == "Switch":
                novo_dispositivo = Switch(nome, marca, modelo, int(self.num_portas_var.get()), self.ip_gestao_var.get())
                novo_dispositivo.port_vlan_map = self.sub_form_switch.get_dados()
            elif tipo == "Servidor":
                endereco_ip = self.endereco_ip_var.get()
                if not endereco_ip: raise ValueError("Servidor deve ter um IP Principal.")
                novo_dispositivo = Servidor(nome, marca, modelo, endereco_ip, self.os_var.get())
                novo_dispositivo.servicos = self.sub_form_servidor.get_dados()
            if self.dispositivo: novo_dispositivo.estado = self.dispositivo.estado
            if self.index is not None: self.app.editar_dispositivo(self.index, novo_dispositivo)
            else: self.app.adicionar_dispositivo(novo_dispositivo)
            self.destroy() 
        except Exception as e:
            messagebox.showerror("Erro ao Guardar", f"Verifique os dados: {e}", parent=self)

def criar_dispositivo_de_dict(item):
    tipo = item.get("Tipo"); dados = item.get("dados_especificos", {}); dispositivo = None
    try:
        if tipo == "Router":
            dispositivo = Router(item.get("Nome"), item.get("Marca"), item.get("Modelo"), dados.get("num_portas", 0))
            dispositivo.interfaces_ip = dados.get("interfaces_ip", [])
        elif tipo == "Switch":
            dispositivo = Switch(item.get("Nome"), item.get("Marca"), item.get("Modelo"), dados.get("num_portas", 0), dados.get("ip_gestao", ""))
            dispositivo.port_vlan_map = dados.get("port_vlan_map", []) 
        elif tipo == "Servidor":
            dispositivo = Servidor(item.get("Nome"), item.get("Marca"), item.get("Modelo"), dados.get("endereco_ip", ""), dados.get("sistema_operativo", ""))
            dispositivo.servicos = dados.get("servicos", [])
        if dispositivo: dispositivo.estado = item.get("Estado", "Desligado")
        return dispositivo
    except Exception as e:
        print(f"Erro ao criar dispositivo {item.get('Nome')}: {e}")
        return None

class GestorFicheiros:
    def __init__(self, app_controller):
        self.app = app_controller
    def guardar_dispositivos(self):
        try:
            filepath = filedialog.asksaveasfilename(initialfile="dispositivos.txt", defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
            if not filepath: return 
            lista_para_guardar = [d.to_dict() for d in self.app.dispositivos]
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(lista_para_guardar, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Exportado", f"Dispositivos guardados com sucesso em '{filepath}'.")
        except Exception as e:
            messagebox.showerror("Erro ao Guardar", f"Não foi possível guardar o ficheiro: {e}")
    def importar_dispositivos(self):
        try:
            filepath = filedialog.askopenfilename(title="Selecionar ficheiro para importar", defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
            if not filepath: return
            if self._carregar_de_ficheiro(filepath):
                messagebox.showinfo("Importado", f"Dispositivos importados com sucesso de '{filepath}'.")
        except Exception as e:
            messagebox.showerror("Erro ao Importar", f"Ocorreu um erro inesperado: {e}")
    def carregar_dispositivos_inicio(self):
        if not os.path.exists(FICHEIRO_AUTOLOAD): return
        self._carregar_de_ficheiro(FICHEIRO_AUTOLOAD, perguntar_substituir=False)
    def _carregar_de_ficheiro(self, filepath, perguntar_substituir=True):
        try:
            with open(filepath, "r", encoding="utf-8") as f: lista_carregada = json.load(f)
            if self.app.dispositivos and perguntar_substituir:
                if not messagebox.askyesno("Confirmar Importação", "Isto irá substituir a lista de dispositivos atual. Deseja continuar?"):
                    return False
            nova_lista = []
            for item in lista_carregada:
                dispositivo = criar_dispositivo_de_dict(item)
                if dispositivo: nova_lista.append(dispositivo)
            self.app.dispositivos = nova_lista
            self.app.filtrar_lista() 
            return True
        except (json.JSONDecodeError, IOError) as e:
            messagebox.showerror("Erro ao Carregar", f"Não foi possível ler ou processar o ficheiro '{filepath}': {e}")
            return False

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Dispositivos de Rede")
        self.root.geometry("1100x600")
        self.dispositivos = []; self.dispositivos_exibidos = []
        self.gestor_ficheiros = GestorFicheiros(self) 
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self._criar_treeview(main_frame)
        self._criar_painel_filtros(main_frame)
        self._criar_botoes_acao(main_frame)
        
        self.gestor_ficheiros.carregar_dispositivos_inicio()

    def _criar_painel_filtros(self, parent):
        filter_frame = ttk.LabelFrame(parent, text="Filtros", padding="10")
        filter_frame.pack(fill=tk.X, pady=5)
        self.filter_nome_var = tk.StringVar(); self.filter_tipo_var = tk.StringVar()
        self.filter_marca_var = tk.StringVar(); self.filter_estado_var = tk.StringVar()
        ttk.Label(filter_frame, text="Nome:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        nome_entry = ttk.Entry(filter_frame, textvariable=self.filter_nome_var, width=20)
        nome_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Label(filter_frame, text="Tipo:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        tipo_combo = ttk.Combobox(filter_frame, textvariable=self.filter_tipo_var, values=["Todos", "Router", "Switch", "Servidor"], width=15)
        tipo_combo.grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)
        ttk.Label(filter_frame, text="Marca:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        marca_combo = ttk.Combobox(filter_frame, textvariable=self.filter_marca_var, values=["Todas"] + MARCAS_PREDEFINIDAS, width=15)
        marca_combo.grid(row=0, column=5, padx=5, pady=5, sticky=tk.EW)
        ttk.Label(filter_frame, text="Estado:").grid(row=0, column=6, padx=5, pady=5, sticky=tk.W)
        estado_combo = ttk.Combobox(filter_frame, textvariable=self.filter_estado_var, values=["Todos", "Ligado", "Desligado"], width=15)
        estado_combo.grid(row=0, column=7, padx=5, pady=5, sticky=tk.EW)
        limpar_btn = ttk.Button(filter_frame, text="Limpar Filtros", command=self.limpar_filtros)
        limpar_btn.grid(row=0, column=8, padx=10, pady=5, sticky=tk.E)
        filter_frame.columnconfigure(1, weight=1); filter_frame.columnconfigure(8, weight=1)
        self.limpar_filtros()
        nome_entry.bind("<KeyRelease>", self.filtrar_lista); tipo_combo.bind("<<ComboboxSelected>>", self.filtrar_lista)
        marca_combo.bind("<<ComboboxSelected>>", self.filtrar_lista); estado_combo.bind("<<ComboboxSelected>>", self.filtrar_lista)
    
    def _criar_botoes_acao(self, parent):
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=5)
        botoes_esquerda = [("Adicionar", self.abrir_janela_adicionar), ("Editar", self.abrir_janela_editar), ("Remover", self.remover_dispositivo)]
        botoes_estado = [("Ligar", lambda: self.toggle_estado(ligar=True)), ("Desligar", lambda: self.toggle_estado(ligar=False))]
        botoes_direita = [("Exportar Como...", self.gestor_ficheiros.guardar_dispositivos), ("Importar de .txt", self.gestor_ficheiros.importar_dispositivos)]
        for (texto, cmd) in botoes_esquerda: ttk.Button(btn_frame, text=texto, command=cmd).pack(side=tk.LEFT, padx=5)
        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        for (texto, cmd) in botoes_estado: ttk.Button(btn_frame, text=texto, command=cmd).pack(side=tk.LEFT, padx=5)
        for (texto, cmd) in reversed(botoes_direita): ttk.Button(btn_frame, text=texto, command=cmd).pack(side=tk.RIGHT, padx=5)

    def _criar_treeview(self, parent):
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        cols = ("Nome", "Tipo", "Estado", "IP/Gestão", "Marca", "Modelo", "Ligações")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
            if col == "Ligações": self.tree.column(col, width=200)
            elif col == "Estado" or col == "Tipo": self.tree.column(col, width=80)
            else: self.tree.column(col, width=140)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.tag_configure("Ligado", background="#C8E6C9", foreground="#003300")
        self.tree.tag_configure("Desligado", background="#FFCDD2", foreground="#550000")

    def popular_lista(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        for i, dispositivo in enumerate(self.dispositivos_exibidos):
            info = dispositivo.mostrar_info()
            ligacoes_str = dispositivo.get_ligacoes_str() 
            valores = (info.get("Nome", "N/A"), info.get("Tipo", "N/A"), info.get("Estado", "N/A"), 
                       dispositivo.get_ip_principal(), info.get("Marca", "N/A"), info.get("Modelo", "N/A"), ligacoes_str)
            self.tree.insert("", tk.END, iid=i, values=valores, tags=(info.get("Estado"),))

    def limpar_filtros(self):
        self.filter_nome_var.set(""); self.filter_tipo_var.set("Todos")
        self.filter_marca_var.set("Todas"); self.filter_estado_var.set("Todos")
        self.filtrar_lista()

    def filtrar_lista(self, event=None):
        f_nome = self.filter_nome_var.get().lower(); f_tipo = self.filter_tipo_var.get()
        f_marca = self.filter_marca_var.get(); f_estado = self.filter_estado_var.get()
        self.dispositivos_exibidos = []
        for dispositivo in self.dispositivos:
            if (f_nome in dispositivo.nome.lower() and
                (f_tipo == "Todos" or dispositivo.__class__.__name__ == f_tipo) and
                (f_marca == "Todas" or dispositivo.marca == f_marca) and
                (f_estado == "Todos" or dispositivo.estado == f_estado)):
                self.dispositivos_exibidos.append(dispositivo)
        self.popular_lista()

    def _get_dispositivo_selecionado(self):
        try:
            selected_item_id = self.tree.selection()[0]
            index_filtrado = int(selected_item_id)
            dispositivo = self.dispositivos_exibidos[index_filtrado]
            index_original = self.dispositivos.index(dispositivo)
            return index_original, dispositivo
        except IndexError:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione um dispositivo da lista.")
            return None, None
        except ValueError:
            messagebox.showerror("Erro de Sincronização", "Erro ao encontrar o dispositivo.")
            return None, None

    def abrir_janela_adicionar(self):
        JanelaDispositivo(self.root, self)
    def abrir_janela_editar(self):
        index, dispositivo = self._get_dispositivo_selecionado()
        if dispositivo: JanelaDispositivo(self.root, self, dispositivo, index)
    def adicionar_dispositivo(self, dispositivo):
        self.dispositivos.append(dispositivo)
        self.filtrar_lista()
    def editar_dispositivo(self, index, dispositivo):
        self.dispositivos[index] = dispositivo
        self.filtrar_lista()
    def remover_dispositivo(self):
        index, dispositivo = self._get_dispositivo_selecionado()
        if dispositivo:
            if messagebox.askyesno("Confirmar Remoção", f"Tem a certeza que quer remover '{dispositivo.nome}'?"):
                self.dispositivos.pop(index)
                self.filtrar_lista()
    def toggle_estado(self, ligar=True):
        index, dispositivo = self._get_dispositivo_selecionado()
        if dispositivo:
            if ligar: dispositivo.ligar()
            else: dispositivo.desligar()
            self.filtrar_lista()

if __name__ == "__main__":
    root = tk.Tk()
    try:
        style = ttk.Style(root)
        if "clam" in style.theme_names(): style.theme_use("clam")
    except Exception: pass
    app = App(root)
    root.mainloop()
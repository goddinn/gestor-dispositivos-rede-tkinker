# Ficheiro: gestor_rede_comentado.py
#
# Descrição: Aplicação gráfica com Tkinter para gestão de dispositivos de rede.
# Permite Adicionar, Editar, Remover, Listar, Ligar/Desligar dispositivos.
# Utiliza Programação Orientada a Objetos (OOP) com herança,
# gestão de ficheiros JSON, e filtragem dinâmica da lista.
#

import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, filedialog
import json
import os

# --- Constantes ---

# Lista de marcas pré-definidas para o dropdown no formulário
MARCAS_PREDEFINIDAS = [
    "Cisco", "Palo Alto", "Huawei", "Juniper", 
    "Dell", "HP", "Arista", "Fortinet", "Check Point", "Outra"
]

# Define o caminho absoluto para o ficheiro de autoload.
# __file__ é o próprio ficheiro .py. os.path.dirname obtém a pasta.
# Isto garante que o script encontra o 'dispositivos.txt' na sua pasta,
# independentemente de onde o script for executado (corrige bug de 'working directory').
script_dir = os.path.dirname(os.path.realpath(__file__))
FICHEIRO_AUTOLOAD = os.path.join(script_dir, "dispositivos.txt")


# --- PARTE 1: MODELO de DADOS (CLASSES OOP) ---

class DispositivoRede:
    """
    Classe base (mãe) para todos os dispositivos de rede.
    Define os atributos e métodos comuns que todas as classes filhas herdarão.
    """
    def __init__(self, nome, marca, modelo):
        """ Construtor da classe base. Chamado quando um novo dispositivo é criado. """
        self.nome = nome
        self.marca = marca
        self.modelo = modelo
        self.estado = "Desligado" # Estado default

    def ligar(self):
        """ Altera o estado do dispositivo para 'Ligado'. """
        self.estado = "Ligado"

    def desligar(self):
        """ Altera o estado do dispositivo para 'Desligado'. """
        self.estado = "Desligado"

    def mostrar_info(self):
        """ Retorna um dicionário com a informação base/comum do dispositivo. """
        return {"Nome": self.nome, "Marca": self.marca, "Modelo": self.modelo,
                "Estado": self.estado, "Tipo": self.__class__.__name__}

    def to_dict(self):
        """ 
        Converte o objeto completo (base + derivado) num dicionário.
        Isto é usado para guardar os dados no ficheiro JSON.
        """
        info = self.mostrar_info()
        # Chama o método 'get_dados_especificos' (que será sobreposto nas classes filhas)
        info['dados_especificos'] = self.get_dados_especificos()
        return info

    # --- Métodos 'Placeholder' (a serem sobrepostos pelas classes filhas) ---
    # Estes métodos fornecem um comportamento default, mas espera-se
    # que as classes filhas (Router, Switch) os re-implementem (polimorfismo).

    def get_dados_especificos(self):
        """ Retorna dados específicos da subclasse (default: nada). """
        return {}

    def get_ip_principal(self):
        """ Obtém o IP principal a ser exibido na lista (default: "N/A"). """
        return "N/A"

    def get_ligacoes_str(self):
        """ Obtém o sumário de ligações para a lista (default: "N/A"). """
        return "N/A"

class Router(DispositivoRede):
    """ Classe para Routers. Herda de DispositivoRede. """
    def __init__(self, nome, marca, modelo, num_portas):
        """ Construtor do Router. """
        # Chama o construtor da classe-mãe (DispositivoRede)
        super().__init__(nome, marca, modelo)
        # Atributos específicos do Router
        self.num_portas = num_portas
        # Lista de dicionários: [{'iface': 'Gi0/1', 'ip': '...', 'mask': '...', 'ligado_a': '...'}, ...]
        self.interfaces_ip = []

    def get_dados_especificos(self):
        """ Sobrepõe o método base para incluir dados específicos do Router. """
        return {"num_portas": self.num_portas, "interfaces_ip": self.interfaces_ip}

    def get_ip_principal(self):
        """ Sobrepõe o método base. Retorna o primeiro IP da lista de interfaces. """
        return self.interfaces_ip[0].get("ip", "Nenhum IP") if self.interfaces_ip else "Nenhum IP"

    def get_ligacoes_str(self):
        """ Sobrepõe o método base. Cria um sumário das ligações das interfaces. """
        # Cria uma lista de strings (ex: "Gi0/1: SW-Core") apenas para itens que têm o campo 'ligado_a' preenchido
        ligacoes = [f"{item.get('iface', '?')}: {item.get('ligado_a')}" for item in self.interfaces_ip if item.get("ligado_a")]
        # Junta a lista com vírgulas
        return ", ".join(ligacoes) if ligacoes else "Nenhuma"

class Switch(DispositivoRede):
    """ Classe para Switches. Herda de DispositivoRede. """
    def __init__(self, nome, marca, modelo, num_portas, ip_gestao=""):
        super().__init__(nome, marca, modelo)
        self.num_portas = num_portas
        self.ip_gestao = ip_gestao
        # Lista de dicionários: [{'porta': 'F0/1', 'vlan': '10', 'ligado_a': '...'}, ...]
        self.port_vlan_map = []

    def get_dados_especificos(self):
        """ Sobrepõe o método base para incluir dados específicos do Switch. """
        return {"num_portas": self.num_portas, "ip_gestao": self.ip_gestao, "port_vlan_map": self.port_vlan_map}

    def get_ip_principal(self):
        """ Sobrepõe o método base. Retorna o IP de gestão. """
        return self.ip_gestao if self.ip_gestao else "N/A"

    def get_ligacoes_str(self):
        """ Sobrepõe o método base. Cria um sumário das ligações das portas. """
        ligacoes = [f"{item.get('porta', '?')}: {item.get('ligado_a')}" for item in self.port_vlan_map if item.get("ligado_a")]
        return ", ".join(ligacoes) if ligacoes else "Nenhuma"

class Servidor(DispositivoRede):
    """ Classe para Servidores. Herda de DispositivoRede. """
    def __init__(self, nome, marca, modelo, endereco_ip, sistema_operativo=""):
        super().__init__(nome, marca, modelo)
        self.endereco_ip = endereco_ip
        self.sistema_operativo = sistema_operativo
        # Lista de dicionários: [{'nome': 'ssh', 'ip': '...', 'placa': 'eth0'}, ...]
        self.servicos = []

    def get_dados_especificos(self):
        """ Sobrepõe o método base para incluir dados específicos do Servidor. """
        return {"endereco_ip": self.endereco_ip, "sistema_operativo": self.sistema_operativo, "servicos": self.servicos}

    def get_ip_principal(self):
        """ Sobrepõe o método base. Retorna o IP principal. """
        return self.endereco_ip


# --- PARTE 2: COMPONENTES DA GUI REUTILIZÁVEIS ---

class SubFormularioMultiplo(ttk.Frame):
    """
    Um widget (componente) de GUI reutilizável que herda de ttk.Frame.
    Combina campos de entrada, botões (Adicionar/Guardar/Remover) e uma Treeview.
    Usado para gerir listas complexas: IPs (Router), VLANs (Switch) e Serviços (Servidor).
    Inclui lógica de "click-to-edit".
    """
    def __init__(self, parent, label, labels_entrada, colunas_tree, num_required_fields=None):
        """
        Construtor do sub-formulário.
        :param parent: O widget pai (a JanelaDispositivo).
        :param label: O título do LabelFrame (ex: "Gestão de IPs").
        :param labels_entrada: Lista de strings para os campos de texto (ex: ["IP:", "Máscara:"]).
        :param colunas_tree: Lista de tuplas para as colunas da Treeview (ex: [("ip", "Endereço IP", 100), ...]).
        :param num_required_fields: Número de campos de entrada que são obrigatórios.
        """
        super().__init__(parent)
        self.lista_dados = [] # Lista de dicionários (os dados reais)
        self.entries = [] # Lista para guardar os widgets Entry (caixas de texto)
        
        # Define quantos campos são obrigatórios (default: todos)
        self.num_required = num_required_fields if num_required_fields is not None else len(labels_entrada)

        form_frame = ttk.LabelFrame(self, text=label)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 1. Criar os campos de entrada (Entry widgets)
        entry_frame = ttk.Frame(form_frame)
        entry_frame.pack(fill=tk.X, pady=5)
        
        num_labels = len(labels_entrada)
        has_optional_fields = num_labels > self.num_required

        for i, texto_label in enumerate(labels_entrada):
            ttk.Label(entry_frame, text=texto_label).pack(side=tk.LEFT, padx=(10, 2))
            is_required = (i < self.num_required)
            
            # Lógica de layout: Se houver campos opcionais (como "Ligado a:"),
            # os campos obrigatórios têm tamanho fixo e os opcionais expandem.
            if has_optional_fields:
                if is_required:
                    # Campo obrigatório (ex: IP, Porta): tamanho fixo
                    entry = ttk.Entry(entry_frame, width=12)
                    entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.NONE, expand=False)
                else:
                    # Campo opcional (ex: "Ligado a:"): expande para preencher
                    entry = ttk.Entry(entry_frame) 
                    entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True) 
            else:
                # Caso (Servidor) onde todos são obrigatórios: expandem igualmente
                entry = ttk.Entry(entry_frame, width=15)
                entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
            self.entries.append(entry)

        # 2. Criar os botões de Ação
        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Adicionar Novo", command=self.adicionar_novo_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Guardar Edição", command=self.guardar_edicao_selecionada).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Remover Selecionado", command=self.remover_item_selecionado).pack(side=tk.LEFT, padx=5)

        # 3. Criar a Treeview (Lista)
        col_ids = [col[0] for col in colunas_tree] # IDs internos (ex: 'iface')
        self.tree = ttk.Treeview(form_frame, columns=col_ids, show="headings", height=8)
        for col_id, col_text, col_width in colunas_tree: # (ex: ('iface', 'Interface', 80))
            self.tree.heading(col_id, text=col_text)
            self.tree.column(col_id, width=col_width)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 4. Bind (associar) o evento de seleção da Treeview ao método _on_item_select
        self.tree.bind("<<TreeviewSelect>>", self._on_item_select)

    def _limpar_entries(self):
        """ Método helper para limpar todas as caixas de texto. """
        for entry in self.entries:
            entry.delete(0, tk.END)

    def _on_item_select(self, event=None):
        """
        Método de callback (evento) chamado quando um item na Treeview é selecionado.
        Popula as caixas de texto com os dados do item clicado ("click-to-edit").
        """
        try:
            # Obter o ID do item selecionado
            selected_item = self.tree.selection()[0]
            # Obter os valores desse item (vem como uma tupla de strings)
            valores = self.tree.item(selected_item, 'values')
            
            # Itera pelas caixas de texto (self.entries) e pelos valores (valores)
            # e preenche cada caixa com o valor correspondente.
            for entry, value in zip(self.entries, valores):
                entry.delete(0, tk.END) # Limpa primeiro
                entry.insert(0, value)  # Insere o valor
        except IndexError:
            # Isto acontece se a seleção for limpa (ex: após remover um item)
            pass # Ignora o erro silenciosamente

    def adicionar_novo_item(self):
        """ Lê os campos de texto, valida, e adiciona um NOVO item à Treeview. """
        valores = [entry.get() for entry in self.entries]
        
        # Valida apenas os campos definidos como obrigatórios
        valores_requeridos = valores[:self.num_required]
        if not all(valores_requeridos):
            messagebox.showwarning("Campos Vazios", f"Preencha pelo menos os primeiros {self.num_required} campos.", parent=self)
            return
            
        col_ids = self.tree.cget("columns")
        dados_dict = dict(zip(col_ids, valores)) # Cria o dicionário de dados
        
        self.lista_dados.append(dados_dict) # Adiciona à lista de dados
        self.tree.insert("", tk.END, values=valores) # Adiciona à Treeview
        
        self._limpar_entries() # Limpa as caixas de texto
        if self.tree.selection(): # Remove a seleção da treeview
            self.tree.selection_remove(self.tree.selection())

    def guardar_edicao_selecionada(self):
        """
        Obtém os dados das caixas de texto
        e ATUALIZA o item atualmente selecionado na Treeview.
        """
        try:
            # Verifica se um item está realmente selecionado
            selected_item = self.tree.selection()[0]
            index = self.tree.index(selected_item) # Obtém o índice (0, 1, 2...)
        except IndexError:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, clique num item da lista para o poder editar.", parent=self)
            return

        # 1. Obter os novos valores das caixas de texto
        novos_valores = [entry.get() for entry in self.entries]
        
        # 2. Validar
        valores_requeridos = novos_valores[:self.num_required]
        if not all(valores_requeridos):
            messagebox.showwarning("Campos Vazios", f"Os primeiros {self.num_required} campos não podem estar vazios.", parent=self)
            return

        # 3. Atualizar a Treeview (interface)
        self.tree.item(selected_item, values=novos_valores)
        
        # 4. Atualizar a lista de dados (self.lista_dados)
        col_ids = self.tree.cget("columns")
        dados_dict = dict(zip(col_ids, novos_valores))
        self.lista_dados[index] = dados_dict # Substitui o item antigo pelo novo
        
        # 5. Limpar
        self._limpar_entries()
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def remover_item_selecionado(self):
        """ Remove o item selecionado da Treeview e da lista de dados. """
        try:
            selected_item = self.tree.selection()[0]
            index = self.tree.index(selected_item)
            
            self.lista_dados.pop(index) # Remove da lista de dados
            self.tree.delete(selected_item) # Remove da Treeview
            
            self._limpar_entries() # Limpa as caixas de texto
            
        except IndexError:
            messagebox.showwarning("Nenhuma Seleção", "Selecione um item da lista para remover.", parent=self)
            
    def preencher_dados(self, dados_lista):
        """ Popula o formulário com dados existentes (usado no modo de edição). """
        self.lista_dados = list(dados_lista) # Cria uma cópia
        col_ids = self.tree.cget("columns")
        for item_dict in self.lista_dados:
            # .get(col_id, "") garante que funciona mesmo se a chave (ex: 'ligado_a') não existir
            valores = [item_dict.get(col_id, "") for col_id in col_ids]
            self.tree.insert("", tk.END, values=valores)

    def get_dados(self):
        """ Retorna a lista de dados (lista de dicionários) para ser guardada. """
        return self.lista_dados


# --- PARTE 3: JANELA DE ADIÇÃO/EDIÇÃO (FORMULÁRIO) ---

class JanelaDispositivo(Toplevel):
    """
    Janela modal (Toplevel) para Adicionar ou Editar um dispositivo.
    O seu conteúdo é gerado dinamicamente.
    """
    def __init__(self, parent, app_controller, dispositivo=None, index=None):
        """
        Construtor da janela.
        :param parent: A janela principal (App).
        :param app_controller: A instância da App (para chamar .adicionar_dispositivo(), etc.).
        :param dispositivo: O objeto Dispositivo a ser editado (None se for Adicionar).
        :param index: O índice do dispositivo a ser editado.
        """
        super().__init__(parent)
        self.transient(parent) # Mantém-se no topo da janela principal
        self.grab_set() # Torna a janela modal (bloqueia a janela principal)
        
        self.app = app_controller; self.dispositivo = dispositivo; self.index = index 
        self.title("Editar Dispositivo" if self.dispositivo else "Adicionar Dispositivo")
        
        # Geometria fixa e não redimensionável
        self.window_width = 600; self.window_height = 700
        self.geometry(f"{self.window_width}x{self.window_height}")
        self.resizable(False, False)
        
        # Variáveis de controlo (StringVar) para os widgets
        self.tipo_var = tk.StringVar(); self.nome_var = tk.StringVar()
        self.marca_var = tk.StringVar(); self.modelo_var = tk.StringVar()
        
        # Referências para os sub-formulários (para obter os dados no on_save)
        self.sub_form_router = self.sub_form_switch = self.sub_form_servidor = None
        
        # Construir a GUI
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        self._criar_campos_comuns(main_frame)
        self.dynamic_frame = ttk.LabelFrame(main_frame, text="Detalhes Específicos")
        self.dynamic_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._criar_botoes(main_frame)
        
        # Define um 'trace' (observador) que chama 'atualizar_campos_dinamicos'
        # sempre que o valor de 'tipo_var' (o dropdown Tipo) muda.
        self.tipo_var.trace("w", self.atualizar_campos_dinamicos)

        # Preencher os dados se estiver em modo de edição, ou definir default se for Adicionar
        if self.dispositivo: self.preencher_formulario()
        else: self.tipo_combo.current(0) # Ativa o 'trace'
        
        # Centrar a janela (último passo)
        self.center_window()

    def center_window(self):
        """ Calcula e define a posição da janela para o centro do ecrã. """
        self.update_idletasks() # Força o tkinter a calcular a geometria
        screen_width = self.winfo_screenwidth(); screen_height = self.winfo_screenheight()
        pos_x = (screen_width // 2) - (self.window_width // 2)
        pos_y = (screen_height // 2) - (self.window_height // 2)
        self.geometry(f"+{pos_x}+{pos_y}") # Define a posição

    def _criar_campos_comuns(self, parent):
        """ Método helper para criar os campos (Nome, Marca, Modelo, Tipo). """
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
        """ Método helper para criar os botões Guardar/Cancelar. """
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
        ttk.Button(btn_frame, text="Guardar", command=self.on_save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def atualizar_campos_dinamicos(self, *args):
        """
        Chamado pelo 'trace' em 'tipo_var'.
        Limpa o 'dynamic_frame' e recria os campos específicos
        para o tipo de dispositivo selecionado.
        """
        for widget in self.dynamic_frame.winfo_children(): widget.destroy()
        self.sub_form_router = self.sub_form_switch = self.sub_form_servidor = None
        tipo = self.tipo_var.get()
        
        # Variáveis de controlo para os campos específicos
        self.num_portas_var = tk.StringVar(); self.ip_gestao_var = tk.StringVar()
        self.endereco_ip_var = tk.StringVar(); self.os_var = tk.StringVar()

        if tipo == "Router":
            frame_portas = ttk.Frame(self.dynamic_frame)
            frame_portas.pack(fill=tk.X, pady=5, padx=5)
            ttk.Label(frame_portas, text="Num. Portas:").pack(side=tk.LEFT, padx=5)
            ttk.Entry(frame_portas, textvariable=self.num_portas_var, width=10).pack(side=tk.LEFT, padx=5)
            # Reutiliza o SubFormularioMultiplo
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
            # Reutiliza o SubFormularioMultiplo
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
            # Reutiliza o SubFormularioMultiplo
            self.sub_form_servidor = SubFormularioMultiplo(self.dynamic_frame, "Gestão de Serviços",
                labels_entrada=["Serviço:", "IP Alocado:", "Placa Rede:"],
                colunas_tree=[("nome", "Serviço", 100), ("ip", "IP Alocado", 120), ("placa", "Placa Rede", 100)],
                num_required_fields=3)
            self.sub_form_servidor.pack(fill=tk.BOTH, expand=True)

    def preencher_formulario(self):
        """ Preenche todos os campos da janela com os dados do 'self.dispositivo'. """
        self.nome_var.set(self.dispositivo.nome); self.marca_var.set(self.dispositivo.marca); self.modelo_var.set(self.dispositivo.modelo)
        tipo = self.dispositivo.__class__.__name__
        self.tipo_var.set(tipo); self.tipo_combo.config(state="disabled") # Desativa o dropdown (não se pode mudar o tipo)
        
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
        """
        Chamado pelo botão 'Guardar'. Valida os dados, cria/atualiza o
        objeto Dispositivo e passa-o para o controlador (App).
        """
        try:
            # 1. Obter dados comuns
            tipo = self.tipo_var.get(); nome = self.nome_var.get(); marca = self.marca_var.get(); modelo = self.modelo_var.get()
            if not all([tipo, nome, marca, modelo]): raise ValueError("Preencha todos os campos comuns.")
            
            # 2. Criar o objeto da classe correta
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
            
            # 3. Manter o estado original se estiver a editar
            if self.dispositivo: novo_dispositivo.estado = self.dispositivo.estado
            
            # 4. Chamar o método da App para guardar
            if self.index is not None:
                self.app.editar_dispositivo(self.index, novo_dispositivo) # Modo Edição
            else:
                self.app.adicionar_dispositivo(novo_dispositivo) # Modo Adição
                
            self.destroy() # Fechar a janela modal
        except Exception as e:
            messagebox.showerror("Erro ao Guardar", f"Verifique os dados: {e}", parent=self)

# --- PARTE 4: GESTOR DE FICHEIROS (LÓGICA DE I/O) ---

def criar_dispositivo_de_dict(item):
    """
    Função 'Factory' (Fábrica).
    Recebe um dicionário (lido do JSON) e retorna uma
    instância da classe de dispositivo correta (Router, Switch, etc.).
    """
    tipo = item.get("Tipo"); dados = item.get("dados_especificos", {}); dispositivo = None
    try:
        # Com base no "Tipo", chama o construtor da classe correta
        if tipo == "Router":
            dispositivo = Router(item.get("Nome"), item.get("Marca"), item.get("Modelo"), dados.get("num_portas", 0))
            dispositivo.interfaces_ip = dados.get("interfaces_ip", [])
        elif tipo == "Switch":
            dispositivo = Switch(item.get("Nome"), item.get("Marca"), item.get("Modelo"), dados.get("num_portas", 0), dados.get("ip_gestao", ""))
            dispositivo.port_vlan_map = dados.get("port_vlan_map", []) 
        elif tipo == "Servidor":
            dispositivo = Servidor(item.get("Nome"), item.get("Marca"), item.get("Modelo"), dados.get("endereco_ip", ""), dados.get("sistema_operativo", ""))
            dispositivo.servicos = dados.get("servicos", [])
        
        if dispositivo: dispositivo.estado = item.get("Estado", "Desligado") # Restaura o estado
        return dispositivo
    except Exception as e:
        print(f"Erro ao criar dispositivo {item.get('Nome')}: {e}")
        return None

class GestorFicheiros:
    """
    Classe que centraliza toda a lógica de I/O (Importar, Exportar, Autoload).
    Mantém a classe App (Controlador) mais limpa.
    """
    def __init__(self, app_controller):
        """ Guarda uma referência à instância principal da App. """
        self.app = app_controller

    def guardar_dispositivos(self):
        """ Abre um diálogo 'Guardar Como' e guarda a lista de dispositivos em JSON. """
        try:
            # Pede ao utilizador para escolher o local e nome do ficheiro
            filepath = filedialog.asksaveasfilename(initialfile="dispositivos.txt", defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
            if not filepath: return # Utilizador cancelou
            
            # Converte todos os objetos na lista mestra para dicionários
            lista_para_guardar = [d.to_dict() for d in self.app.dispositivos]
            
            # Escreve a lista de dicionários no ficheiro usando json.dump
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(lista_para_guardar, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Exportado", f"Dispositivos guardados com sucesso em '{filepath}'.")
        except Exception as e:
            messagebox.showerror("Erro ao Guardar", f"Não foi possível guardar o ficheiro: {e}")

    def importar_dispositivos(self):
        """ Abre um diálogo 'Abrir' e carrega os dispositivos desse ficheiro. """
        try:
            filepath = filedialog.askopenfilename(title="Selecionar ficheiro para importar", defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
            if not filepath: return # Utilizador cancelou
            
            # Chama a lógica central de carregamento
            if self._carregar_de_ficheiro(filepath):
                messagebox.showinfo("Importado", f"Dispositivos importados com sucesso de '{filepath}'.")
        except Exception as e:
            messagebox.showerror("Erro ao Importar", f"Ocorreu um erro inesperado: {e}")

    def carregar_dispositivos_inicio(self):
        """ Carrega o ficheiro 'dispositivos.txt' default ao iniciar a app. """
        if not os.path.exists(FICHEIRO_AUTOLOAD):
            #print(f"Ficheiro de autoload '{FICHEIRO_AUTOLOAD}' não encontrado.")
            return # Falha silenciosamente se o ficheiro não existir
        self._carregar_de_ficheiro(FICHEIRO_AUTOLOAD, perguntar_substituir=False)

    def _carregar_de_ficheiro(self, filepath, perguntar_substituir=True):
        """
        Lógica central de leitura de ficheiro.
        Lê o ficheiro, faz o parse do JSON, recria os objetos
        e atualiza a lista mestra na App.
        """
        try:
            # Lê o ficheiro e faz o parse do JSON para uma lista de dicionários
            with open(filepath, "r", encoding="utf-8") as f: lista_carregada = json.load(f)
            
            # Se já houver dados e for uma importação manual, pergunta antes de substituir
            if self.app.dispositivos and perguntar_substituir:
                if not messagebox.askyesno("Confirmar Importação", "Isto irá substituir a lista de dispositivos atual. Deseja continuar?"):
                    return False # Utilizador cancelou
                    
            nova_lista = []
            for item in lista_carregada:
                dispositivo = criar_dispositivo_de_dict(item) # Usa a factory
                if dispositivo: nova_lista.append(dispositivo)
            
            # Substitui a lista mestra na App
            self.app.dispositivos = nova_lista
            # Aplica os filtros (que por sua vez pop_a a lista)
            self.app.filtrar_lista() 
            return True
        except (json.JSONDecodeError, IOError) as e:
            # Captura erros de ficheiro corrompido ou não encontrado
            messagebox.showerror("Erro ao Carregar", f"Não foi possível ler ou processar o ficheiro '{filepath}': {e}")
            return False

# --- PARTE 5: APLICAÇÃO PRINCIPAL (GUI E CONTROLO) ---

class App:
    """ 
    Classe principal da aplicação. Gere a janela mestra (root),
    o estado da aplicação (listas) e atua como o controlador principal.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Dispositivos de Rede")
        self.root.geometry("1100x600") # Tamanho da janela principal
        
        # self.dispositivos = A lista MESTRA com TODOS os dispositivos
        self.dispositivos = []
        # self.dispositivos_exibidos = A lista FILTRADA que o utilizador vê
        self.dispositivos_exibidos = []
        
        # Instancia o gestor de ficheiros, passando uma referência de si própria
        self.gestor_ficheiros = GestorFicheiros(self) 
        
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # CORREÇÃO DE BUG: A Treeview (lista) DEVE ser criada ANTES
        # do painel de filtros, senão os filtros falham ao tentar
        # popular uma lista que ainda não existe.
        self._criar_treeview(main_frame)
        self._criar_painel_filtros(main_frame)
        self._criar_botoes_acao(main_frame)
        
        # Carrega os dados do ficheiro 'dispositivos.txt'
        self.gestor_ficheiros.carregar_dispositivos_inicio()

    def _criar_painel_filtros(self, parent):
        """ Cria o LabelFrame com os controlos de filtro. """
        filter_frame = ttk.LabelFrame(parent, text="Filtros", padding="10")
        filter_frame.pack(fill=tk.X, pady=5)
        
        # Variáveis de controlo para os filtros
        self.filter_nome_var = tk.StringVar(); self.filter_tipo_var = tk.StringVar()
        self.filter_marca_var = tk.StringVar(); self.filter_estado_var = tk.StringVar()
        
        # Layout em Grelha (Grid) para alinhar os widgets
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
        
        # Configura as colunas 1 e 8 para expandir, empurrando os controlos
        filter_frame.columnconfigure(1, weight=1); filter_frame.columnconfigure(8, weight=1)
        
        # Define os valores default (que chama filtrar_lista)
        self.limpar_filtros()
        
        # Associa eventos (bind) para que a filtragem seja automática
        nome_entry.bind("<KeyRelease>", self.filtrar_lista) # A cada tecla
        tipo_combo.bind("<<ComboboxSelected>>", self.filtrar_lista) # A cada seleção
        marca_combo.bind("<<ComboboxSelected>>", self.filtrar_lista)
        estado_combo.bind("<<ComboboxSelected>>", self.filtrar_lista)
    
    def _criar_botoes_acao(self, parent):
        """ Cria a barra de botões (Adicionar, Editar, Ligar, Exportar, etc.). """
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
        """ Cria a lista (Treeview) principal e as suas colunas. """
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        cols = ("Nome", "Tipo", "Estado", "IP/Gestão", "Marca", "Modelo", "Ligações")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        
        for col in cols:
            self.tree.heading(col, text=col)
            # Define larguras diferentes para as colunas
            if col == "Ligações": self.tree.column(col, width=200)
            elif col == "Estado" or col == "Tipo": self.tree.column(col, width=80)
            else: self.tree.column(col, width=140)
            
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Tags de cor para o estado (Ligado/Desligado)
        self.tree.tag_configure("Ligado", background="#C8E6C9", foreground="#003300")
        self.tree.tag_configure("Desligado", background="#FFCDD2", foreground="#550000")

    def popular_lista(self):
        """
        Limpa e re-popula a Treeview.
        Esta função lê *apenas* da lista 'self.dispositivos_exibidos' (a lista filtrada).
        """
        for row in self.tree.get_children(): self.tree.delete(row)
        
        for i, dispositivo in enumerate(self.dispositivos_exibidos):
            info = dispositivo.mostrar_info()
            ligacoes_str = dispositivo.get_ligacoes_str() 
            valores = (info.get("Nome", "N/A"), info.get("Tipo", "N/A"), info.get("Estado", "N/A"), 
                       dispositivo.get_ip_principal(), info.get("Marca", "N/A"), info.get("Modelo", "N/A"), ligacoes_str)
            # O 'iid' (ID do item) é o índice 'i' da lista *filtrada*
            self.tree.insert("", tk.END, iid=i, values=valores, tags=(info.get("Estado"),))

    def limpar_filtros(self):
        """ Reseta os campos de filtro e re-filtra a lista. """
        self.filter_nome_var.set(""); self.filter_tipo_var.set("Todos")
        self.filter_marca_var.set("Todas"); self.filter_estado_var.set("Todos")
        self.filtrar_lista() # Re-executa a filtragem

    def filtrar_lista(self, event=None):
        """
        Função principal de filtragem.
        Compara a lista mestra 'self.dispositivos' com os filtros
        e guarda o resultado em 'self.dispositivos_exibidos'.
        """
        f_nome = self.filter_nome_var.get().lower(); f_tipo = self.filter_tipo_var.get()
        f_marca = self.filter_marca_var.get(); f_estado = self.filter_estado_var.get()
        
        self.dispositivos_exibidos = [] # Limpa a lista de exibição
        
        for dispositivo in self.dispositivos: # Itera sobre a lista MESTRA
            # Aplica os 4 filtros. Se algum falhar, 'continue' salta para o próximo dispositivo.
            if (f_nome not in dispositivo.nome.lower() and
                (f_tipo == "Todos" or dispositivo.__class__.__name__ != f_tipo) and
                (f_marca == "Todas" or dispositivo.marca != f_marca) and
                (f_estado == "Todos" or dispositivo.estado != f_estado)):
                continue
                
            # Se passou em todos os testes, adiciona à lista de exibição
            self.dispositivos_exibidos.append(dispositivo)
            
        self.popular_lista() # Atualiza a Treeview com os resultados

    def _get_dispositivo_selecionado(self):
        """
        Helper que traduz a seleção na Treeview (lista filtrada)
        para o objeto e o seu índice na lista mestra (self.dispositivos).
        """
        try:
            selected_item_id = self.tree.selection()[0]
            # 1. Obtém o índice da lista FILTRADA (o 'iid' que definimos)
            index_filtrado = int(selected_item_id)
            # 2. Obtém o objeto real dessa lista
            dispositivo = self.dispositivos_exibidos[index_filtrado]
            # 3. Encontra o índice desse objeto na lista MESTRA
            index_original = self.dispositivos.index(dispositivo)
            
            return index_original, dispositivo
        except IndexError:
            # Captura o erro se self.tree.selection() estiver vazio
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione um dispositivo da lista.")
            return None, None
        except ValueError:
            # Captura erro de sincronização se o item não for encontrado na lista mestra
            messagebox.showerror("Erro de Sincronização", "Erro ao encontrar o dispositivo.")
            return None, None

    def abrir_janela_adicionar(self):
        """ Abre a janela de adição. """
        JanelaDispositivo(self.root, self)

    def abrir_janela_editar(self):
        """ Abre a janela de edição com os dados do item selecionado. """
        index, dispositivo = self._get_dispositivo_selecionado()
        if dispositivo: JanelaDispositivo(self.root, self, dispositivo, index)

    def adicionar_dispositivo(self, dispositivo):
        """ Adiciona um novo dispositivo à lista MESTRA e re-filtra. """
        self.dispositivos.append(dispositivo)
        self.filtrar_lista() # Re-filtra para atualizar a vista

    def editar_dispositivo(self, index, dispositivo):
        """ Atualiza um dispositivo na lista MESTRA e re-filtra. """
        self.dispositivos[index] = dispositivo
        self.filtrar_lista()

    def remover_dispositivo(self):
        """ Remove um dispositivo da lista MESTRA e re-filtra. """
        index, dispositivo = self._get_dispositivo_selecionado()
        if dispositivo:
            if messagebox.askyesno("Confirmar Remoção", f"Tem a certeza que quer remover '{dispositivo.nome}'?"):
                self.dispositivos.pop(index)
                self.filtrar_lista()

    def toggle_estado(self, ligar=True):
        """ Altera o estado (Ligar/Desligar) de um dispositivo e re-filtra. """
        index, dispositivo = self._get_dispositivo_selecionado()
        if dispositivo:
            if ligar: dispositivo.ligar()
            else: dispositivo.desligar()
            self.filtrar_lista() # Re-filtra (caso o utilizador esteja a filtrar por estado)

# --- PONTO DE ENTRADA DA APLICAÇÃO ---
if __name__ == "__main__":
    """
    Ponto de entrada principal.
    Cria a janela 'root', define um estilo (tema) e inicia a App.
    Este bloco só é executado quando o ficheiro é corrido diretamente.
    """
    root = tk.Tk()
    try:
        # Tenta usar um tema visual melhor (se disponível)
        style = ttk.Style(root)
        if "clam" in style.theme_names(): style.theme_use("clam")
    except Exception: pass # Falha silenciosamente se não houver temas
    
    app = App(root)
    root.mainloop() # Inicia o loop de eventos da GUI (mantém a janela aberta)
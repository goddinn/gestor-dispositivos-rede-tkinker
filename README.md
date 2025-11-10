# gestor-dispositivos-rede-tkinker

Projeto  
Gestor de Dispositivos de Rede 
Objetivo: Criar uma aplicação gráfica em Python (Tkinter) que permita gerir dispositivos de rede 
Aplicar Programação Orientada a Objetos e herança. 
Requisitos do Projeto: 
1.  Classe base DispositivoRede:  
• Atributos: 
nome, endereço_ip, estado; 
• métodos: 
ligar(), desligar(), mostrar_info(). 
•2. Classes derivadas: 
• Router: acrescenta atributo num_portas 
•  Switch: acrescenta atributo num_vlans 
• Servidor: acrescenta atributo serviço_principal. (desempenho de funções) 
3.  Interface Tkinter 
• com campos para tipo, nome, IP e atributo adicional. 
4. Funções para: 
• adicionar, listar, ligar, desligar e guardar os dispositivos num ficheiro .txt. 
5. Aplicar super() nas classes derivadas e implementar tratamento de erros. 
6. Guardar e carregar dados de ficheiro (desafio opcional). 
Desafios adicionais : 
• Janela secundária com detalhes do dispositivo. 
• Ordenar dispositivos por tipo ou estado. 
• Interface com ícones e cores diferentes por tipo. 

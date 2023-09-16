import customtkinter
import cv2
import os
import tkinter
import time
import pymoos
import socket
import numpy as np
import socket
import io
from auvlib.data_tools import jsf_data, utils
from tkintermapview import TkinterMapView
from PIL import Image, ImageTk
from pyais import decode


# Configuração do AIS da PRT
ip_address = '201.76.184.242' 
port = 8000

# Create a TCP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
sock.connect((ip_address, port))


customtkinter.set_default_color_theme("blue")
customtkinter.set_appearance_mode("Dark")


class App(customtkinter.CTk):

    APP_NAME = "AVP-MOOS v0.1"
    WIDTH = 1000
    HEIGHT = 800

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title(App.APP_NAME)
        self.geometry(str(App.WIDTH) + "x" + str(App.HEIGHT))
        self.minsize(App.WIDTH, App.HEIGHT)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Command-q>", self.on_closing)
        self.bind("<Command-w>", self.on_closing)
        self.createcommand('tk::mac::Quit', self.on_closing)

        #Socket para conectar ao sonar
        self.sonar_ip = "127.0.0.1"
        self.sonar_port = 3000
        self.sonar_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sonar_socket.bind((self.sonar_ip, self.sonar_port))
        
        #Variável auxiliar para ligar AIS da praticagem
        self.check_var = tkinter.StringVar(self,"off")

        #Auxilio na plotagem dos AIS
        self.marker_list = []

        #Init pymoos comms
        self.comms = pymoos.comms()

        #Variáveis do sonar plot
        self.waterfall_img = None
        self.markers_sonar = None
        #self.markers_sonar = {} #Dicionário para marcações do sonar
        self.contador_sonar = 0 #Contador de marcações sonar

        #Variáveis auxiliares
        self.mmsi_list = []
        self.markers_ais = {} #Dicionário para colocar os marcadores
        self.markers_image = {} #Dicionário para imagens dos navios AIS
        self.camera_on = False
        self.nav_lat = 0
        self.nav_long = 0
        self.nav_heading = 0
        self.nav_speed = 0
        self.last_ais_msg = None

        #Carrego imagens para os ícones
        self.current_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        #Imagem do meu navio
        self.ship_imagefile = Image.open(os.path.join(self.current_path, "images", "ship_red0.png"))
        ship_image = ImageTk.PhotoImage(self.ship_imagefile)

        # ============ create two CTkFrames ============

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame_left = customtkinter.CTkFrame(master=self, width=150, corner_radius=0, fg_color=None)
        self.frame_left.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        self.frame_right = customtkinter.CTkFrame(master=self, corner_radius=0)
        self.frame_right.grid(row=0, column=1, rowspan=1, pady=0, padx=0, sticky="nsew")

        # ============ frame_left ============
        self.frame_left.grid_rowconfigure(6, weight=1) #Para deixar igualmente espaçados
        self.frame_left.grid_rowconfigure(7, weight=1)
        self.frame_left.grid_rowconfigure(8, weight=1)
        self.frame_left.grid_rowconfigure(9, weight=1)

        self.button_1 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Colocar Marcador",
                                                command=self.set_marker_event)
        self.button_1.grid(pady=(20, 0), padx=(20, 20), row=0, column=0)

        self.button_2 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Limpar Marcadores",
                                                command=self.clear_marker_event)
        self.button_2.grid(pady=(20, 0), padx=(20, 20), row=1, column=0)

        self.button_3 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Câmera",
                                                command=self.open_camera)
        self.button_3.grid(pady=(20, 0), padx=(20, 20), row=2, column=0)

        self.button_4 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Desativar Mapas",
                                                command=self.destroy_maps)
        self.button_4.grid(pady=(20, 0), padx=(20, 20), row=3, column=0)

        self.button_5 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Controle Remoto",
                                                command=self.activate_control)
        self.button_5.grid(pady=(20, 0), padx=(20, 20), row=4, column=0)

        self.sss_button = customtkinter.CTkButton(master=self.frame_left,
                                                text="SSS",
                                                command=self.activate_sss)
        self.sss_button.grid(pady=(20, 0), padx=(20, 20), row=5, column=0)

        self.plot_sonar_button = customtkinter.CTkButton(master=self.frame_left,
                                                text="Sonar Plot",
                                                command=self.receive_sonar)
        self.plot_sonar_button.grid(pady=(20, 0), padx=(20, 20), row=6, column=0)

        #Texto da Latitude

        self.label_lat = customtkinter.CTkLabel(master=self.frame_left, text="Latitude: "+str(self.nav_lat))
        self.label_lat.configure(font=("Segoe UI", 15))
        self.label_lat.grid(row=7, column=0,  padx=(20,20), pady=(50,0), sticky="")

        #Texto da Longitude

        self.label_long = customtkinter.CTkLabel(master=self.frame_left, text="Longitude: "+str(self.nav_long))
        self.label_long.configure(font=("Segoe UI", 15))
        self.label_long.grid(row=7, column=0,  padx=(20,20), pady=(0,20), sticky="")

        #Texto do rumo

        self.label_heading = customtkinter.CTkLabel(master=self.frame_left, text="Rumo: "+str(self.nav_heading))
        self.label_heading.configure(font=("Segoe UI", 25))
        self.label_heading.grid(row=8, column=0,  padx=(20,20), pady=(20,20), sticky="")

        #Texto da veloc

        self.label_speed = customtkinter.CTkLabel(master=self.frame_left, text="Velocidade: "+str(self.nav_speed)+" nós",)
        self.label_speed.configure(font=("Segoe UI", 25))
        self.label_speed.grid(row=9, column=0,  padx=(20,20), pady=(20,20), sticky="")

        

        self.map_label = customtkinter.CTkLabel(self.frame_left, text="Servidor de Mapas:", anchor="w")
        self.map_label.grid(row=10, column=0, padx=(20, 20), pady=(20, 0))
        self.map_option_menu = customtkinter.CTkOptionMenu(self.frame_left, values=["OpenStreetMap", "Google normal", "Google satellite"],
                                                                       command=self.change_map)
        self.map_option_menu.grid(row=11, column=0, padx=(20, 20), pady=(10, 0))

        self.appearance_mode_label = customtkinter.CTkLabel(self.frame_left, text="Aparência:", anchor="w")
        self.appearance_mode_label.grid(row=12, column=0, padx=(20, 20), pady=(20, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.frame_left, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode)
        self.appearance_mode_optionemenu.grid(row=13, column=0, padx=(20, 20), pady=(10, 20))

        

        # ============ frame_right ============

        self.frame_right.grid_rowconfigure(1, weight=1)
        self.frame_right.grid_rowconfigure(0, weight=0)
        self.frame_right.grid_columnconfigure(0, weight=1)
        self.frame_right.grid_columnconfigure(1, weight=0)
        self.frame_right.grid_columnconfigure(2, weight=1)
        
        #Criação do mapa inicial
        self.script_directory = os.path.dirname(os.path.abspath(__file__))
        self.database_path = os.path.join(self.script_directory, "offline_tiles_rio.db")
        self.map_widget = TkinterMapView(self.frame_right, corner_radius=0,use_database_only=True,database_path=self.database_path)
        self.map_widget.grid(row=1, rowspan=1, column=0, columnspan=3, sticky="nswe", padx=(0, 0), pady=(0, 0))
        self.map_widget.set_overlay_tile_server("http://tiles.openseamap.org/seamark//{z}/{x}/{y}.png")

        self.entry = customtkinter.CTkEntry(master=self.frame_right,
                                            placeholder_text="Digite Endereço")
        self.entry.grid(row=0, column=0, sticky="we", padx=(12, 0), pady=12)
        self.entry.bind("<Return>", self.search_event)

        self.button_6 = customtkinter.CTkButton(master=self.frame_right,
                                                text="Buscar",
                                                width=90,
                                                command=self.search_event)
        self.button_6.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=12)

        self.botao_centralizar_navio = customtkinter.CTkButton(master=self.frame_right,
                                                text="Centralizar Navio",
                                                width=90,
                                                command=self.centralizar_navio)
        self.botao_centralizar_navio.grid(row=0, column=2, sticky="w", padx=(12, 0), pady=12)

        
        #Botão que liga/desliga AIS da praticagem
        self.checkbox = customtkinter.CTkCheckBox(master=self.frame_left, text="AIS Praticagem", command=self.update_lista_praticagem(),variable=self.check_var, onvalue="on", offvalue="off")
        self.checkbox.grid(row=14, column=0, padx=(20, 20), pady=(10, 20))

        ###Imagem da camera
        self.vid = cv2.VideoCapture('teste.mp4')
        self.camera_width , self.camera_height = 800,600

        # Set the width and height
        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)

        # Create a label and display it on app
        self.text_var = tkinter.StringVar(value="")
        self.label_widget = customtkinter.CTkLabel(self,textvariable=self.text_var)
        self.label_widget.grid(row=0,column=2,sticky="nsew",rowspan=1,columnspan=3)


        # Set default values
        self.map_widget.set_position(-22.911663710002028, -43.15942144574782) #Posição inicial do mapa
        self.map_widget.set_zoom(15) 
        #self.map_widget.set_address("Rio de Janeiro")
        self.map_option_menu.set("Google normal")
        self.appearance_mode_optionemenu.set("Dark")

        #Teste de marcadores
        self.marker_1 = self.map_widget.set_marker(-22.910369249774234, -43.15891349244546, text="VSNT-Lab", icon=ship_image, command=self.marker_callback)

        #Conexão com a database do MOOS
        
        self.comms.set_on_connect_callback(self.onc)
        self.comms.set_on_mail_callback(self.onm)
        self.comms.run('localhost', 9000, 'avp-moos')

        #Loop para atualizar a posição do navio
        
        #Loop principal
        self.update_ship_position() #Loop para atualizar a posição do navio
        self.update_gui() #Loop para atualizar dados na GUI
        self.update_ais_contacts() #Loop para atualizar os contatos AIS
        #self.update_lista_praticagem() #Loop para atualizar a lista de praticagem



    def activate_sss(self):
        os.popen('python3 funcionando_recebendo_img.py')

    #Função para centralizar o navio na tela
    def centralizar_navio(self):
        self.map_widget.set_position(self.nav_lat,self.nav_long)

    #Função para converter de graus para graus, minutos e segundos
    def decimal_degrees_to_dms(self,latitude):
        degrees = int(latitude)
        decimal_minutes = (latitude - degrees) * 60
        minutes = int(decimal_minutes)
        seconds = (decimal_minutes - minutes) * 60
        return degrees, minutes, seconds

    #Funções para comunicação do Pymoos
    def onc(self):
        self.comms.register('NAV_LAT', 0)
        self.comms.register('NAV_LONG', 0)
        self.comms.register('NAV_HEADING', 0)
        self.comms.register('NAV_SPEED', 0)
        #self.comms.register('LAST_AIS_MSG', 0)
        self.comms.register('MSG_UDP', 0)
        return True
    
    def onm(self):
        msg_list = self.comms.fetch()

        for msg in msg_list:
            val = msg.double()

            if msg.name() == 'NAV_LAT':
                self.nav_lat = val
                #print(self.nav_lat)
            elif msg.name() == 'NAV_LONG':
                self.nav_long = val
            elif msg.name() == 'NAV_HEADING':
                self.nav_heading = val
            elif msg.name() == 'NAV_SPEED':
                self.nav_speed = val
            elif msg.name() == 'MSG_UDP':
                val = msg.string()
                #print(val)
                if val.startswith('!AIVDM'):
                    #self.last_ais_msg = val
                    print(val)
                
            
        return True
    
    
    #Atualiza a lista de ctts AIS q vem da praticagem - Lembrar sempre de executar funções no final do programa
    
    def update_lista_praticagem(self): 
        if self.check_var.get() == "on":
            global sock
            data = sock.recv(1024)
            if not data:
                pass
            print("Received:", data.decode())
            mensagens_ais = data.decode().split('\r\n')
            #Create a marker for each ais message
            if (self.map_widget.winfo_exists() == 1): #Verifica se o mapa existe
                for msg in mensagens_ais:
                    decoded_msg = self.decode_ais_msg(msg) #Decodifico a msg
                    if decoded_msg is not None and hasattr(decoded_msg, 'heading') and decoded_msg.mmsi not in self.mmsi_list: #Caso não esteja na lista
                        self.mmsi_list.append(decoded_msg.mmsi) #Adiciono na lista
                        #Crio o marker
                        if int(decoded_msg.heading) > 360: 
                            decoded_msg.heading = int(decoded_msg.heading) - 360 #Corrige o ângulo do navio caso seja maior q 360
                        self.markers_image[decoded_msg.mmsi] = Image.open(os.path.join(self.current_path, "images", "ship_green"+str(int(decoded_msg.heading))+".png"))
                        ship_image = ImageTk.PhotoImage(self.markers_image[decoded_msg.mmsi])
                        self.markers_ais[decoded_msg.mmsi] = self.map_widget.set_marker(decoded_msg.lat, decoded_msg.lon, text="Contato_"+str(decoded_msg.mmsi), icon=ship_image, command=self.marker_callback)
                    elif hasattr(decoded_msg, 'heading') and decoded_msg is not None: #Caso já esteja na lista o navio
                        #Atualizo o marcador
                        self.markers_ais[decoded_msg.mmsi].set_position(decoded_msg.lat,decoded_msg.lon)
                        if int(decoded_msg.heading) > 360: 
                            decoded_msg.heading = int(decoded_msg.heading) - 360 #Corrige o ângulo do navio caso seja maior q 360
                        self.markers_image[decoded_msg.mmsi] = Image.open(os.path.join(self.current_path, "images", "ship_green"+str(int(decoded_msg.heading))+".png"))
                        ship_image = ImageTk.PhotoImage(self.markers_image[decoded_msg.mmsi])
                        self.markers_ais[decoded_msg.mmsi].change_icon(ship_image)
        else:
            pass


        self.after(1000,self.update_lista_praticagem) #Coloco essa função em loop para repetir a cada 1 seg dentro do programa

    #Plota a imagem vinda do sonar na carta náutica
    def receive_sonar(self):
        #Recebo a imagem pelo socket
        bufferSize = 1024
        bytesAddressPair = self.sonar_socket.recvfrom(bufferSize)
        message = bytesAddressPair[0]
        image_data = b""
        image_data += message
        
        image_stream = io.BytesIO(image_data)
        image = Image.open(image_stream).convert('RGBA')
        #Rotaciono a imagem
        #if int(self.nav_heading) > 180:
        #angulo_image = (int(self.nav_heading)+90) % 360

        #Combino com a imagem grande
        if self.waterfall_img is None:
            self.waterfall_img = image
        else: 
            dst = Image.new('RGBA', (self.waterfall_img.width, self.waterfall_img.height + image.height))
            dst.paste(self.waterfall_img, (0, 0))
            dst.paste(image, (0, self.waterfall_img.height))
            self.waterfall_img = dst

        #image = image.rotate(angulo_image,expand=True)

        photo = ImageTk.PhotoImage(self.waterfall_img)
        
        #create a marker in map with photo
        if (self.map_widget.winfo_exists() == 1): #Verifica se o mapa existe
            #Plota a imagem recebida pelo sonar
            #Crio um marker fixo
            if self.markers_sonar is None:
                self.markers_sonar= self.map_widget.set_marker(self.nav_lat, self.nav_long, icon=photo)
                #mudo a posição do icone
                self.markers_sonar.icon_anchor = 'n'
            else: #Atualiza a imagem
                self.markers_sonar.change_icon(photo)

            
            #Aumenta o contador
            #self.contador_sonar +=1
            #self.map_widget.set_marker(-22.910369249774234, -43.15891349244546, icon=photo)
        
        self.after(100,self.receive_sonar) #A cada 0,1 segundo ele vai receber posição sonar
            

    
    
    #TODO Adicionar função que ao clicar em um contato AIS abra um pop-up mostrando informações do navio
    #Decodificar msgs AIS - Coloquei estático pq a função decode não usa self
    @staticmethod
    def decode_ais_msg(ais_msg):
        ais_msg = ais_msg.encode()
        #Catch errors and let them pass
        try:
            ais_msg = decode(ais_msg)
        except:
            ais_msg = None #Por enquanto vou retornar None caso esteja com erro
            pass
        return ais_msg
        

    #Função para atualizar os contatos AIS
    def update_ais_contacts(self):
        #Decodifico a msg AIS
        if self.last_ais_msg is not None:
            ais_msg = self.last_ais_msg
            self.last_ais_msg = self.decode_ais_msg(ais_msg) 

        #Crio o marker no mapa
        if (self.map_widget.winfo_exists() == 1): #Verifica se o mapa existe
            if self.last_ais_msg is not None and self.last_ais_msg.mmsi not in self.mmsi_list: #Verifica se o mmsi já não está na lista
                #Adiciono código mmsi a lista
                self.mmsi_list.append(self.last_ais_msg.mmsi)
                #Imagem do marcador - coloquei isso pq alguns vinham maior q 360
                if int(self.last_ais_msg.heading) > 360: 
                    self.last_ais_msg.heading = int(self.last_ais_msg.heading) - 360 #Corrige o ângulo do navio caso seja maior q 360
                self.markers_image[self.last_ais_msg.mmsi] = Image.open(os.path.join(self.current_path, "images", "ship_green"+str(int(self.last_ais_msg.heading))+".png"))
                ship_image = ImageTk.PhotoImage(self.markers_image[self.last_ais_msg.mmsi])
                
                #Crio o marcador 
                self.markers_ais[self.last_ais_msg.mmsi] = self.map_widget.set_marker(self.last_ais_msg.lat, self.last_ais_msg.lon, text="Contato_"+str(self.last_ais_msg.mmsi), icon=ship_image, command=self.marker_callback)
                
            elif self.last_ais_msg is not None: #Caso o navio já esteja na lista
                #Atualizo a posição do marcador
                self.markers_ais[self.last_ais_msg.mmsi].set_position(self.last_ais_msg.lat,self.last_ais_msg.lon)
                #Atualizo a imagem do marcador
                if int(self.last_ais_msg.heading) > 360: 
                    self.last_ais_msg.heading = int(self.last_ais_msg.heading) - 360 #Corrige o ângulo do navio caso seja maior q 360
                self.markers_image[self.last_ais_msg.mmsi] = Image.open(os.path.join(self.current_path, "images", "ship_green"+str(int(self.last_ais_msg.heading))+".png"))
                ship_image = ImageTk.PhotoImage(self.markers_image[self.last_ais_msg.mmsi])
                self.markers_ais[self.last_ais_msg.mmsi].change_icon(ship_image)
        self.after(1000,self.update_ais_contacts) #Coloco essa função em loop para repetir a cada 1 seg dentro do programa

        
        

    
    #Função para atualizar dados na GUI:
    def update_gui(self):
        degrees, minutes, seconds = self.decimal_degrees_to_dms(self.nav_lat)
        self.label_lat.configure(text=f"Latitude: {degrees}° {minutes}' {seconds:.2f}\"")
        degrees, minutes, seconds = self.decimal_degrees_to_dms(self.nav_long)
        self.label_long.configure(text=f"Longitude: {degrees}° {minutes}' {seconds:.2f}\"")
        self.label_heading.configure(text="Rumo: "+str(int(self.nav_heading))+" °")
        self.label_speed.configure(text="Velocidade: "+str(int(self.nav_speed))+" nós")
        self.after(1000,self.update_gui)


    #Função em loop utilizada para atualizar a posição do meu navio
    def update_ship_position(self):
        if (self.map_widget.winfo_exists() == 1): #Checa se existe o mapa
            self.marker_1.set_position(self.nav_lat,self.nav_long)
            #self.map_widget.set_position(self.nav_lat,self.nav_long) #Centraliza o mapa no navio, colocar uma opção para ativar ela 
            #self.map_widget.set_zoom(15)
            self.label_widget.configure(text=str(self.nav_lat)+" "+str(self.nav_long))

            #Atualiza a imagem do navio de acordo com o ângulo self.nav_heading
            self.ship_imagefile = Image.open(os.path.join(self.current_path, "images", "ship_red"+str(int(self.nav_heading))+".png"))
            ship_image = ImageTk.PhotoImage(self.ship_imagefile)
            self.marker_1.change_icon(ship_image)
        else:
            print("Mapa inativo")

        self.after(1000,self.update_ship_position) #Coloco essa função em loop para repetir a cada 1 seg dentro do programa


    #Funções da GUI abaixo

    def marker_callback(self,marker): #O que acontece quando clica no marker
        print(marker.text)


    def destroy_control(self): #Destrói o frame com o controle
        self.button_5.configure(command=self.activate_control,text="Controle Remoto")
        self.slider_progressbar_frame.destroy()
        self.label_machine.destroy()
        self.label_leme.destroy()
        self.label_controle.destroy()
        self.progressbar_2.destroy()
        self.progressbar_3.destroy()
        self.slider_1.destroy()
        self.slider_2.destroy()
        #self.combobox.destroy()

        

    def activate_control(self): #Cria o frame com o controle
        self.button_5.configure(command=self.destroy_control,text="Desativar Controle Remoto")
        #Frame com slider para controle de velocidade   

        # create slider and progressbar frame
        self.slider_progressbar_frame = customtkinter.CTkFrame(self, fg_color="transparent",width=200,height=200)
        self.slider_progressbar_frame.grid(row=0, column=5, padx=(20, 0), pady=(90, 0), sticky="nsew") #Mexer no pady se quiser abaixar mais o frame
        self.slider_progressbar_frame.grid_columnconfigure(0, weight=1)
        self.slider_progressbar_frame.grid_rowconfigure(5, weight=0)
        self.slider_progressbar_frame.grid_rowconfigure(6, weight=2)
        self.slider_progressbar_frame.grid_rowconfigure(1, weight=1)
        
        #Label do Controle Remoto
        self.label_machine = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text="Controle Remoto")
        self.label_machine.configure(font=("Segoe UI", 30))
        self.label_machine.grid(row=0, column=0, columnspan=1, padx=(10,0), pady=(10,30), sticky="")

        #Label do Leme
        self.label_machine = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text="Leme")
        self.label_machine.configure(font=("Segoe UI", 20))
        self.label_machine.grid(row=3, column=0, columnspan=1, padx=(10,0), pady=(10,20), sticky="")

        #Label das Máquinas
        
        self.label_machine = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text="Máquinas")
        self.label_machine.configure(font=("Segoe UI", 20))
        self.label_machine.grid(row=1, column=0, columnspan=1, padx=(190,0), pady=(20,20), sticky="")

        self.progressbar_2 = customtkinter.CTkProgressBar(self.slider_progressbar_frame,width=300)
        self.progressbar_2.grid(row=5, column=0, padx=(20, 10), pady=(0, 0),sticky="nsew")
        
        self.slider_1 = customtkinter.CTkSlider(self.slider_progressbar_frame, from_=-30, to=30, number_of_steps=60)
        self.slider_1.grid(row=4, column=0, padx=(20, 10), pady=(15, 15), sticky="ew")
        self.slider_2 = customtkinter.CTkSlider(self.slider_progressbar_frame, from_=0, to=1, number_of_steps=100, orientation="vertical",height=400)
        self.slider_2.grid(row=0, column=1, rowspan=5, padx=(10, 15), pady=(20, 10))
        self.slider_2.set(0) #Zero o slider de máquinas
        self.progressbar_3 = customtkinter.CTkProgressBar(self.slider_progressbar_frame, orientation="vertical",height=400)
        self.progressbar_3.grid(row=0, column=2, rowspan=5, padx=(10, 20), pady=(20, 10))

        #Configurando a barra de progresso
        self.slider_1.configure(command=self.update_value_leme) #Configurei o slider para setar a barra de progresso
        self.progressbar_3.set(self.slider_2.get())
        self.slider_2.configure(command=self.update_value_maquinas)

        #Porcentagem de Máquinas 
        self.label_machine = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text=str(int(self.slider_2.get()*100))+"%")
        self.label_machine.configure(font=("Segoe UI", 15))
        self.label_machine.grid(row=0, column=2, columnspan=1, padx=(5,15), pady=(5,5), sticky="n")

        #Angulo do Leme
        self.label_leme = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text=str(int(self.slider_1.get()))+"°")
        self.label_leme.configure(font=("Segoe UI", 25))
        self.label_leme.grid(row=6, column=0, columnspan=2,rowspan=1, padx=(5,10), pady=(0,10), sticky="s")

        #Escolha de modo de controle remoto
        
        #Texto
        self.label_controle = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text="Modo de controle")
        self.label_controle.configure(font=("Segoe UI", 25))
        self.label_controle.grid(row=9, column=0, rowspan=1, columnspan=2, padx=(5,10), pady=(60,15), sticky="")
        
        #Menu para escolha
        self.combobox = customtkinter.CTkOptionMenu(master=self.slider_progressbar_frame,
                                       values=["Manual", "Teclado", "Joystick"],
                                       command=self.optionmenu_callback)
        self.combobox.grid(row=10, column=0, rowspan=1,columnspan=2, padx=(5,10), pady=(0,205), sticky="")


    def optionmenu_callback(self,choice):
        print("optionmenu dropdown clicked:", choice)

    def update_value_maquinas(self,other):
        print(other)
        self.progressbar_3.set(self.slider_2.get())
        self.label_machine.configure(text=str(int(self.slider_2.get()*100))+"%")

    def update_value_leme(self,other):
        print(other)
        self.progressbar_2.set(self.slider_1.get())
        self.label_leme.configure(text=str(int(self.slider_1.get()))+"°")
        

    def destroy_maps(self):
        self.map_widget.destroy() #Deleta o mapa
        self.entry.destroy() #Deleta a pesquisa
        self.button_6.destroy() #Deleta o botão de pesquisa
        self.button_4.configure(command=self.open_maps,text="Ativar Mapas") #Configura o botão para ativar os mapas novamente
        #self.frame_right.grid_columnconfigure(3, weight=2) #Configura o grid para que o label da câmera ocupe todo o espaço
        self.label_widget.grid(row=0, rowspan=1, column=1, columnspan=3, sticky="nswe") #Coloco a câmera no centro

        

    def open_maps(self):
        self.label_widget.grid(row=0, rowspan=1, column=2, columnspan=3, sticky="nswe") #Câmera no canto
        
        #Cria o mapa
        
        self.map_widget = TkinterMapView(self.frame_right, corner_radius=0,use_database_only=True,database_path=self.database_path)
        self.map_widget.grid(row=1, rowspan=1, column=0, columnspan=3, sti
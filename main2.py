import customtkinter
import cv2
import os
import tkinter
import time
import pymoos
from tkintermapview import TkinterMapView
from PIL import Image, ImageTk


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

        self.marker_list = []

        #Init pymoos comms
        self.comms = pymoos.comms()

        #Variáveis auxiliares
        self.camera_on = False

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

        self.frame_left.grid_rowconfigure(5, weight=1)

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

        

        self.map_label = customtkinter.CTkLabel(self.frame_left, text="Servidor de Mapas:", anchor="w")
        self.map_label.grid(row=6, column=0, padx=(20, 20), pady=(20, 0))
        self.map_option_menu = customtkinter.CTkOptionMenu(self.frame_left, values=["OpenStreetMap", "Google normal", "Google satellite"],
                                                                       command=self.change_map)
        self.map_option_menu.grid(row=7, column=0, padx=(20, 20), pady=(10, 0))

        self.appearance_mode_label = customtkinter.CTkLabel(self.frame_left, text="Aparência:", anchor="w")
        self.appearance_mode_label.grid(row=8, column=0, padx=(20, 20), pady=(20, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.frame_left, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode)
        self.appearance_mode_optionemenu.grid(row=9, column=0, padx=(20, 20), pady=(10, 20))

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
                                                text="Search",
                                                width=90,
                                                command=self.search_event)
        self.button_6.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=12)

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
        self.marker_1 = self.map_widget.set_marker(-22.910369249774234, -43.15891349244546, text="Meu Navio", icon=ship_image, command=self.marker_callback)

        #Conexão com a database do MOOS
        
        self.comms.set_on_connect_callback(self.onc)
        self.comms.set_on_mail_callback(self.onm)
        self.comms.run('localhost', 9000, 'avp-moos')

        #Loop para atualizar a posição do navio
        #Variáveis iniciais
        self.nav_lat = 0
        self.nav_long = 0
        self.nav_heading = 0
        #Loop principal
        self.update_ship_position()

    #Funções para comunicação do Pymoos
    def onc(self):
        self.comms.register('NAV_LAT', 0)
        self.comms.register('NAV_LONG', 0)
        self.comms.register('NAV_HEADING', 0)
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
            
        return True
    
    #Função em loop utilizada para atualizar a posição do meu navio
    def update_ship_position(self):
        if (self.map_widget.winfo_exists() == 1): #Checa se existe o mapa
            self.marker_1.set_position(self.nav_lat,self.nav_long)
            self.map_widget.set_position(self.nav_lat,self.nav_long) #Centraliza o mapa no navio, colocar uma opção para ativar ela 
            #self.map_widget.set_zoom(15)
            self.label_widget.configure(text=str(self.nav_lat)+" "+str(self.nav_long))

            #Atualiza a imagem do navio de acordo com o ângulo self.nav_heading
            self.ship_imagefile = Image.open(os.path.join(self.current_path, "images", "ship_red"+str(int(self.nav_heading))+".png"))
            ship_image = ImageTk.PhotoImage(self.ship_imagefile)
            self.marker_1.change_icon(ship_image)
        else:
            print("Mapa inativo")

        self.after(1000,self.update_ship_position)


    #Funções da GUI abaixo

    def marker_callback(self,marker):
        print(marker.text)
        coordinates = [
        (-22.910369249774234, -43.15891349244546),
        (-22.910480263848627, -43.15912266093175),
        (-22.910613862916277, -43.15931490120975),
        (-22.910754142521347, -43.15948326987964),
        (-22.910887741588997, -43.15964915604181),
        (-22.911019573899215, -43.15982732964322),
        (-22.911150820070173, -43.16000388549634),
        (-22.91128104658741, -43.16018438349646),
        (-22.911413870960102, -43.16036625051805),
        (-22.911547741266644, -43.160550184006156)
        ]
        
        if self.i==9:
            self.i == 0
        else:
            self.i+=1
        
        marker.set_position(coordinates[self.i][0],coordinates[self.i][1])

        #Rotate ship
        #self.ship_imagefile = Image.open(os.path.join(self.current_path, "images", "ship_red0.png"))
        self.r+=15
        self.ship_imagefile = Image.open(os.path.join(self.current_path, "images", "ship_red"+str(self.r)+".png"))
        ship_image = ImageTk.PhotoImage(self.ship_imagefile)
        marker.change_icon(ship_image)
        
        #marker.delete()

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
        self.map_widget.grid(row=1, rowspan=1, column=0, columnspan=3, sticky="nswe", padx=(0, 0), pady=(0, 0))
        self.map_widget.set_overlay_tile_server("http://tiles.openseamap.org/seamark//{z}/{x}/{y}.png")

        self.entry = customtkinter.CTkEntry(master=self.frame_right,
                                            placeholder_text="Digite Endereço")
        self.entry.grid(row=0, column=0, sticky="we", padx=(12, 0), pady=12)
        self.entry.bind("<Return>", self.search_event)

        self.button_6 = customtkinter.CTkButton(master=self.frame_right,
                                                text="Search",
                                                width=90,
                                                command=self.search_event)
        self.button_6.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=12)

        #Plota o meu navio
        self.ship_imagefile = Image.open(os.path.join(self.current_path, "images", "ship_red"+str(int(self.nav_heading))+".png"))
        self.ship_image = ImageTk.PhotoImage(self.ship_imagefile)
        self.marker_1 = self.map_widget.set_marker(self.nav_lat, self.nav_long, text="VSNT-Lab", icon=self.ship_image, command=self.marker_callback)
        self.marker_1.change_icon(self.ship_image)
        

        #Crio a barra de pesquisas
        
        self.entry = customtkinter.CTkEntry(master=self.frame_right,
                                            placeholder_text="Digite o Endereço")
        self.entry.grid(row=0, column=0, sticky="we", padx=(12, 0), pady=12)
        self.entry.bind("<Return>", self.search_event)

        self.button_6 = customtkinter.CTkButton(master=self.frame_right,
                                                text="Busca",
                                                width=90,
                                                command=self.search_event)
        self.button_6.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=12)
        self.button_4.configure(command=self.destroy_maps,text="Desativar Mapas")

    def destroy_camera(self):
        self.label_widget.destroy() #Destruo o label da câmera
        self.button_3.configure(command=self.destroy_camera,text="Câmera")
        #Crio o label de novo
        self.label_widget = customtkinter.CTkLabel(self,textvariable=self.text_var)
        if (self.map_widget.winfo_exists() == 1): #Checa se o mapa está ativo
            self.label_widget.grid(row=0, rowspan=1, column=2, columnspan=3, sticky="nswe")
        else:
            self.label_widget.grid(row=0, rowspan=1, column=1, columnspan=3, sticky="nswe")
        self.button_3.configure(command=self.open_camera) #Configuro para abrir a câmera novamente

    def open_camera(self):
            self.button_3.configure(command=self.destroy_camera,text="Desativar Câmera") #Coloco o botão para tirar a câmera
  
            # Capture the video frame by frame
            _, frame = self.vid.read()
        
            # Convert image from one color space to other
            opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        
            # Capture the latest frame and transform to image
            captured_image = Image.fromarray(opencv_image)
        
            # Convert captured image to photoimage
            photo_image = ImageTk.PhotoImage(image=captured_image)
        
            # Displaying photoimage in the label
            self.label_widget.photo_image = photo_image
        
            # Configure image in the label
            self.label_widget.configure(image=photo_image)
        
            # Repeat the same process after every 10 seconds
            self.label_widget.after(10, self.open_camera)


    def search_event(self, event=None):
        self.map_widget.set_address(self.entry.get())

    def set_marker_event(self):
        current_position = self.map_widget.get_position()
        self.marker_list.append(self.map_widget.set_marker(current_position[0], current_position[1]))

    def clear_marker_event(self):
        for marker in self.marker_list:
            marker.delete()

    def change_appearance_mode(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_map(self, new_map: str):
        if new_map == "OpenStreetMap":
            self.map_widget.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
            self.map_widget.set_overlay_tile_server("http://tiles.openseamap.org/seamark//{z}/{x}/{y}.png")
        elif new_map == "Google normal":
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
            self.map_widget.set_overlay_tile_server("http://tiles.openseamap.org/seamark//{z}/{x}/{y}.png")
        elif new_map == "Google satellite":
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
            self.map_widget.set_overlay_tile_server("http://tiles.openseamap.org/seamark//{z}/{x}/{y}.png")

    def on_closing(self, event=0):
        self.destroy()

    def start(self):
        self.mainloop()


if __name__ == "__main__":
    app = App()
    app.start()
import pymoos
import pyproj
import time

class testeMOOS(pymoos.comms):

    def __init__(self, moos_community, moos_port):
        """Initiates MOOSComms, sets the callbacks and runs the loop"""
        super(testeMOOS, self).__init__()
        self.server = moos_community
        self.port = moos_port
        self.name = 'testeMOOS'
        self.iter = 0

        #Variáveis auxiliares
        self.mmsi_list = []
        self.markers_ais = {} #Dicionário para colocar os marcadores
        self.markers_image = {} #Dicionário para imagens dos navios AIS
        self.camera_on = False
        self.nav_lat = 0
        self.nav_long = 0
        self.nav_yaw = 0 #leme do navio
        self.nav_heading = 0
        self.nav_speed = 0
        self.last_ais_msg = None
        self.controle_manual = False
        self.contador_ativacao_controle = 0
        self.view_seglist = None
        self.view_point = None
        self.ponto_ativo_marker = None
        self.station_keep_marker = None
        self.deploy = None
        self.return_var = None
        self.bhv_settings = None #Comportamento ativo no momento
        self.ivphelm_bhv_active = None 


        self.set_on_connect_callback(self.__on_connect)
        self.set_on_mail_callback(self.__on_new_mail)
        self.run(self.server, self.port, self.name)

    def __on_connect(self):
        #Variáveis do MOOS para exibição do navio 
        self.register('NAV_LAT', 0)
        self.register('NAV_LONG', 0)
        self.register('NAV_HEADING', 0)
        self.register('NAV_SPEED', 0)
        self.register('NAV_YAW', 0)
        self.register('MSG_UDP', 0)

        #Variáveis do MOOS para controle do navio
        self.register('DEPLOY', 0)
        self.register('MOOS_MANUAL_OVERIDE', 0)
        self.register('RETURN', 0)
        self.register('DESIRED_RUDDER', 0)
        self.register('DESIRED_THRUST', 0)

        #Variáveis do MOOS para o controle autônomo
        self.register('VIEW_SEGLIST', 0) #rela de pontos
        self.register('VIEW_POINT', 0) #Ponto autônomo ativo no momento
        self.register('BHV_SETTINGS', 0) #Comportamento ativo no momento
        self.register('IVPHELM_BHV_ACTIVE', 0) #Comportamento ativo no momento

        return True

    def __on_new_mail(self):
        msg_list = self.fetch()

        for msg in msg_list:
            val = msg.double()

            if msg.name() == 'NAV_LAT':
                self.nav_lat = val
            elif msg.name() == 'NAV_LONG':
                self.nav_long = val
            elif msg.name() == 'NAV_HEADING':
                self.nav_heading = val
            elif msg.name() == 'NAV_SPEED':
                self.nav_speed = val
            elif msg.name() == 'VIEW_SEGLIST':
                val = msg.string()
                self.view_seglist = val
                #print(val)
            elif msg.name() == 'NAV_YAW': #Leme do navio
                self.nav_yaw = val
                #print(val)
            elif msg.name() == 'VIEW_POINT': #Ponto autônomo ativo no momento
                val = msg.string()
                self.view_point = val
            elif msg.name() == 'DEPLOY':
                val = msg.string()
                self.deploy = val
            elif msg.name() == 'BHV_SETTINGS': 
                val = msg.string()
                self.bhv_settings = val
                #print('Comportamento ativo no momento: '+self.bhv_settings)
            elif msg.name() == 'IVPHELM_BHV_ACTIVE':
                val = msg.string()
                self.ivphelm_bhv_active = val
                print(ivphelm_bhv_active)
            elif msg.name() == 'RETURN':
                val = msg.string()
                self.return_var = val         
            
        return True

    def send_points(self):
        x = 120
        y = 70
        #string_update = f"polygon={float(x)},{float(y)}"
        string_update = "points=60,-40:60,-160 # speed = 2.0"
        if self.deploy == 'false' or self.return_var == 'true':
            self.notify('DEPLOY', 'true',pymoos.time())
            self.notify('MOOS_MANUAL_OVERIDE', 'false',pymoos.time())
            self.notify('RETURN', 'false',pymoos.time())
        self.notify('WPT_UPDATE', string_update,pymoos.time())  
        #self.notify('VIEW_SEGLIST', string_update,pymoos.time())
        print(string_update)
        self.notify('END','false',pymoos.time())  

IP_MOOS = "localhost" 
PORTA_MOOS = 9000

# Dados para o lago do MIT
LatOrigin  = 43.825300 
LongOrigin = -70.330400 

def main():
    tester = testeMOOS(IP_MOOS, PORTA_MOOS)

    while True:
        time.sleep(1)
        tester.send_points()

if __name__ == "__main__":
    main()
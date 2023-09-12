import pymoos
import pyproj
import time

IP_MOOS = "localhost" 
PORTA_MOOS = 9000
LOCATION = "MIT"

class MissionControl(pymoos.comms):

    def __init__(self, moos_community, moos_port, location):
        """
        Initiates MOOSComms, sets the callbacks and runs the loop
        """
        super(MissionControl, self).__init__()
        self.server = moos_community
        self.port = moos_port
        self.name = 'missionControl'
        self.iter = 0
        self.location = location

        # Setup variables
        self.nav_lat = 0
        self.nav_long = 0
        self.nav_yaw = 0 
        self.nav_heading = 0
        self.nav_speed = 0
        self.nav_depth = 0
        self.last_ais_msg = None
        self.view_seglist = None
        self.view_point = None
        self.deploy = None
        self.return_var = None
        self.bhv_settings = None # Current behavior
        self.ivphelm_bhv_active = None 

        self.__set_local_coordinates()

        self.set_on_connect_callback(self.__on_connect)
        self.set_on_mail_callback(self.__on_new_mail)
        status = self.run(self.server, self.port, self.name)

        self.init_time = pymoos.time()
        print(f"Connection status is: {status} at {self.init_time}")

    def __set_local_coordinates(self):  
        """
        Possible locations = {"Salvador"
                              "Rio de Janeiro"
                              "MIT"}
        """
        if self.location == "Rio de Janeiro":
            self.LatOrigin = -22.93335 
            self.LongOrigin = -43.136666665 
        elif self.location == "Salvador":
            self.LatOrigin = -12.97933112028696
            self.LongOrigin = -38.5666610393065            
        elif self.location == "MIT":
            self.LatOrigin  = 43.825300 
            self.LongOrigin = -70.330400 

        self.projection_local = pyproj.Proj(proj='aeqd', ellps='WGS84',
                                datum='WGS84', lat_0=self.LatOrigin, lon_0=self.LongOrigin)
        self.projection_global = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')
        
        # The below parameters where set with trial and error due to a difference
        # between real world and moos simulation
        self.diff_x = 25.1
        self.diff_y = 38.6

    def __on_connect(self):
        """
        Register MOOS variables when connecting to server
        """
        # Vessel Variables
        self.register('NAV_LAT', 0)
        self.register('NAV_LONG', 0)
        self.register('NAV_HEADING', 0)
        self.register('NAV_SPEED', 0)
        self.register('NAV_DEPTH', 0)
        self.register('NAV_YAW', 0)
        self.register('MSG_UDP', 0)

        # Control Variables
        self.register('DEPLOY', 0)
        self.register('MOOS_MANUAL_OVERIDE', 0)
        self.register('RETURN', 0)
        self.register('DESIRED_RUDDER', 0)
        self.register('DESIRED_THRUST', 0)

        # Autonomous Navigation Variables
        self.register('VIEW_SEGLIST', 0) 
        self.register('VIEW_POINT', 0) 
        self.register('BHV_SETTINGS', 0)
        self.register('IVPHELM_BHV_ACTIVE', 0) 

        return True

    def __on_new_mail(self):
        """
        Callback to register incoming messages
        """
        self.last_msg_time = pymoos.time()

        msg_list = self.fetch()

        for msg in msg_list:
            val = msg.double()

            if msg.name() == 'NAV_LAT':
                self.nav_lat = val
            elif msg.name() == 'NAV_LONG':
                self.nav_long = val
            elif msg.name() == 'NAV_HEADING':
                self.nav_heading = val
            elif msg.name() == 'NAV_DEPTH':
                self.nav_depth = val
            elif msg.name() == 'NAV_SPEED':
                self.nav_speed = val
            elif msg.name() == 'VIEW_SEGLIST':
                val = msg.string()
                self.view_seglist = val
            elif msg.name() == 'NAV_YAW': # Vessel's rudder
                self.nav_yaw = val
            elif msg.name() == 'VIEW_POINT': # Current autonomous target point
                val = msg.string()
                self.view_point = val
            elif msg.name() == 'DEPLOY':
                val = msg.string()
                self.deploy = val
            elif msg.name() == 'BHV_SETTINGS': 
                val = msg.string()
                self.bhv_settings = val
            elif msg.name() == 'IVPHELM_BHV_ACTIVE':
                val = msg.string()
                self.ivphelm_bhv_active = val
                print(self.ivphelm_bhv_active)
            elif msg.name() == 'RETURN':
                val = msg.string()
                self.return_var = val       

        return True
    
    def set_navigation_path(self, global_points, desired_speed):
        """
        Sends the desired navigation path to pHelmIVP
        It sets DEPLOY to true and MOOS_MANUAL_OVERIDE to false so it can
        start autonomous navigation

        The string_update to send to WPT_UPDATE must be in the form:
        "points=60,-40:60,-160 # speed = 2.0"

        The received points must be in LAT and LONG
        """

        local_points = self.convert_global2local(global_points)

        # Convert each tuple to a formatted string
        formatted_points = [f"{x},{y}" for x, y in local_points]
        # Join the formatted points using ":"
        result = " : ".join(formatted_points)
        string_update = f"points={result} # speed={desired_speed}"

        self.notify('DEPLOY', 'true',pymoos.time())
        self.notify('MOOS_MANUAL_OVERIDE', 'false',pymoos.time())
        self.notify('RETURN', 'false',pymoos.time())
        # Notify WPT_UPDATE of the desired trajectory
        self.notify('WPT_UPDATE', string_update,pymoos.time())  
        print(string_update)
        self.notify('END','false',pymoos.time())  

    def stop_autonomous_navigation(self):
        """
        Communicates pHelmIvP to stop the autonomous path
        """
        self.notify('END', 'true',pymoos.time())
        self.notify('RETURN', 'true',pymoos.time())
        self.notify('MOOS_MANUAL_OVERIDE', 'true',pymoos.time())
        self.notify('FEEDBACK_MSG', 'completed',pymoos.time())

    def convert_local2global(self,points):
        """
        Convert the local coordinates to global LAT and LONG
        """
        global_points = [pyproj.transform(self.projection_local, self.projection_global, long, lat) for lat,long in points]
        return global_points
    
    def convert_global2local(self,points):
        """
        Convert LAT and LONG to local coordinates
        """
        local_points = [pyproj.transform(self.projection_global, self.projection_local, long, lat) for lat,long in points]
        return local_points

    def activate_remote_control(self):
        """
        Activates user manual control
        """
        self.notify('DEPLOY', 'true',pymoos.time()) 
        self.notify('MOOS_MANUAL_OVERIDE', 'true',pymoos.time())
        
    def notify_thruster(self,desired_thrust):
        """
        Notifies the DESIRED_THRUST value
        """
        self.notify('DESIRED_THRUST',desired_thrust,pymoos.time())

    def notify_rudder(self,desired_rudder):
        """
        Notifies the DESIRED_RUDDER value
        """
        self.notify('DESIRED_RUDDER',desired_rudder,pymoos.time())

    def notify_gear(self,desired_gear):
        """
        Notifies the DESIRED_GEAR value
        """
        self.notify('DESIRED_GEAR',desired_gear,pymoos.time())

    def emergency_stop(self):
        """
        Stops the acceleration, sends gear to neutral and rudder to 0 degrees
        """
        self.notify('MOOS_MANUAL_OVERIDE', 'true',pymoos.time())
        self.notify_thruster(0)
        self.notify_rudder(0)
        self.notify_gear(0)

    def set_desired_speed(self,desired_speed):
        """
        Set the desired_speed for the controller 
        <desired_speed> in meters/s
        """
        self.notify('DESIRED_SPEED', desired_speed, pymoos.time())

def main():
    controller = MissionControl(IP_MOOS, PORTA_MOOS, LOCATION)

    global_points = [(43.824840,-70.330388),(43.824853,-70.329767)]
    desired_speed = 3

    while True:
        controller.set_navigation_path(global_points, desired_speed)
        time.sleep(1)

if __name__ == "__main__":
    main()
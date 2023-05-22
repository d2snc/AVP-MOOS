import pymoos

# Init Pymoos comms
comms = pymoos.comms()

# Variáveis globais
nav_lat = None
nav_long = None
nav_heading = None

def onc():
    comms.register('NAV_LAT', 0)
    comms.register('NAV_LONG', 0)
    comms.register('NAV_HEADING', 0)
    return True

def onm():
    global nav_lat
    global nav_long
    global nav_heading

    msg_list = comms.fetch()

    for msg in msg_list:
        val = msg.double()

        if msg.name() == 'NAV_LAT':
            nav_lat = val
        elif msg.name() == 'NAV_LONG':
            nav_long = val
        elif msg.name() == 'NAV_HEADING':
            nav_heading = val

    return True

def main():
    global nav_lat
    global nav_long
    global nav_heading

    # Kickoff Pymoos callbacks
    comms.set_on_connect_callback(onc)
    comms.set_on_mail_callback(onm)
    comms.run('localhost', 9000, 'avp-moos')

    while True:
        if nav_lat is not None:
            print('NAV_LAT = %f' % nav_lat)
        if nav_long is not None:
            print('NAV_LONG = %f' % nav_long)
        if nav_heading is not None:
            print('NAV_HEADING = %f' % nav_heading)

main()
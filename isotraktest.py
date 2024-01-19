import sys
from time import sleep
from isotrakserver import IsotrakServer

if len(sys.argv) < 2:
    eprint("Usage:", sys.argv[0], "<serial-port>")
    sys.exit()

isoserv = IsotrakServer()
isoserv.port = sys.argv[1]

while True:
    while not isoserv.connect():
        print('Could not connected to serial port', isoserv.port)
        print('Retrying in 5s', end='', flush=True)
        for i in range(1,10):
            print('.', end='', flush=True)
            sleep(0.5)
        print('\n')

    print('Connected to serial port', isoserv.port)

    print('Sending initialization commands to Isotrak')
    isoserv.initialize()
    print('Isotrak initialized; streaming tracker data...')

    while isoserv.connect():
        if isoserv.update():
            isoserv.print()
    
    print('Connection lost, attempting to reestablish on port', isoserv.port)
    continue

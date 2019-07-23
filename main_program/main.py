import sys
sys.path.insert(0, '/var/root/PycharmProjects/metec_model')
from metecmodel import Model
from labjackemulator import LabJack
from main_program.labjackthread import LabJackThread
import socket

if __name__ == '__main__':

    model = Model('../Resources/sensor_properties.csv', '../Resources/GSH-1-volumes.json', initial_pressure=50,
                  initial_temperature=30)

    labjack_names_ports = {
        'GSH-1.LJ-1': 501,
        'CB-1W.LJ-1': 502,
        'CB-1T.LJ-1': 503,
        'CB-1S.LJ-1': 504,
        'CB-2W.LJ-1': 505,
        'CB-2T.LJ-1': 506,
        'CB-2S.LJ-1': 507
    }

    labjack_threads = []

    for name, port in labjack_names_ports.items():
        labjack = LabJack(name, '../Resources/pins_to_registers.csv',
                          '../Resources/sensor_properties.csv', model, port, localhost=False,
                          socket_type=socket.SOCK_STREAM)
        lj_thread = LabJackThread(labjack)
        labjack_threads.append(lj_thread)
        lj_thread.start()

    try:
        while True:
            try:
                char = input('\nE for get emissions\n'
                             'C to check if components are connected\n'
                             'R to read a component\n'
                             'N to get a components neighbors\n'
                             'F to calculate flows\n'
                             'P to set model pressure (psi)\n'
                             'T to set model temperature (F)\n'
                             'V to set a valve state\n'
                             'Q to quit\n')
                char = char.upper()
                if char == 'E':
                    cb = input('Enter the controller box name: ')
                    emissions = model.get_controller_box_emissions(cb)
                    for i in range(0, 3):
                        print('Row {}, {} - scfh'.format(i, emissions[i]))
                if char == 'Q':
                    print('Exiting...')
                    for lj_thread in labjack_threads:
                        lj_thread.stop()
                    exit()
                if char == 'C':
                    first_component = input('Input the name of the first component: ')
                    second_component = input('Input the name of the first component: ')
                    print(model.are_connected(first_component, second_component))
                if char == 'N':
                    component = input('Input component name: ')
                    print(model.graph.graph.edges(component))
                if char == 'R':
                    component = input('Input component name: ')
                    reading = model.get_component(component).get_reading()
                    print(reading)
                if char == 'F':
                    gashouse = input('Input gas house name: ')
                    flows = model.calculate_flows(gashouse)
                    for k, v in flows.items():
                        print('Meter: {}, Flow: {:.4f} - slpm'.format(k, v))
                if char == 'P':
                    pressure = float(input('Enter new model pressure: '))
                    model.change_model_pressure(pressure)
                if char == 'T':
                    temp = float(input('Enter new temperature: '))
                    model.change_model_temperature(temp)
                if char == 'V':
                    valve_name = input('Enter the valve name: ')
                    state = input("'open' or 'close': ")
                    print('Valve now:', model.set_valve(valve_name, state))
            except Exception as e:
                print(e)
    except KeyboardInterrupt:
        print('Execution interrupted, exiting now...')
        for lj_thread in labjack_threads:
            lj_thread.stop()
        exit()

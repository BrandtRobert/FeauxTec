import sys
sys.path.insert(0, '/var/root/PycharmProjects/metec_model')
from metecmodel import Model
from labjackemulator import LabJack
from main_program.labjackthread import LabJackThread
import socket
import yaml


def load_config_file(filename):
    with open(filename, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
            return config
        except yaml.YAMLError as exc:
            print('Error in loading the config file {}'.format(filename))
            print(exc)
            exit(1)


if __name__ == '__main__':
    config = load_config_file('../Resources/config/model_config.yaml')
    model = Model(config['sensor_properties'], config['volumes_files'], config['gashouses'],
                  initial_pressure=config['initial_pressures'], initial_temperature=config['initial_temperatures'])

    for valve, state in config['valve_states'].items():
        model.set_valve(valve, state)

    labjack_names_ports = config['Labjacks']
    socket_type = socket.SOCK_STREAM if config['socket_type'] == 'TCP' else socket.SOCK_DGRAM
    labjack_threads = []

    for name, port in labjack_names_ports.items():
        labjack = LabJack(name, config['pins_to_registers'], config['sensor_properties'], model, port,
                          localhost=config['localhost'], socket_type=socket_type, noise_factor=config['noise_factor'])
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
                    second_component = input('Input the name of the second component: ')
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
                    gashouse = input('Enter the gas house name: ').upper()
                    pressure = float(input('Enter new model pressure: '))
                    model.change_model_pressure(pressure, gashouse)
                if char == 'T':
                    gashouse = input('Enter the gas house name: ').upper()
                    temp = float(input('Enter new temperature: '))
                    model.change_model_temperature(temp, gashouse)
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

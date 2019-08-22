import sys
import socket
import yaml
import time
sys.path.insert(0, '/var/root/PycharmProjects/metec_model')
from metecmodel import Model, StatisticsCollector
from labjackemulator import LabJack
from main_program.labjackthread import LabJackThread
from logger import Logger
from metecmodel.networkgraph import NetworkModel


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
    config = load_config_file('../Resources/config/model_config_3.yaml')
    model = Model(config['sensor_properties'], config['volumes_files'], config['gashouses'],
                  initial_pressure=config['initial_pressures'], initial_temperature=config['initial_temperatures'],
                  failures=config.get('component_failures', {}))

    for valve, state in config['valve_states'].items():
        model.set_valve(valve, state)

    labjack_names_data = config['Labjacks']
    socket_type = socket.SOCK_STREAM if config['socket_type'] == 'TCP' else socket.SOCK_DGRAM
    labjack_threads = []
    labjacks = {}
    print('Creating {} LabJacks'.format(len(labjack_names_data)))
    for name, data in labjack_names_data.items():
        port = data['port']
        failures = data.get('failures', {})
        labjack = LabJack(name, config['pins_to_registers'], config['sensor_properties'], model, port,
                          localhost=config['localhost'], socket_type=socket_type, noise_factor=config['noise_factor'],
                          failures=failures)
        labjacks[name] = labjack
        lj_thread = LabJackThread(labjack)
        labjack_threads.append(lj_thread)
        lj_thread.start()

    network_model = NetworkModel('../Resources/networkgraphs/networkgraph_1.json', labjacks)

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
                             'S to get statistics\n'
                             'G write the current graph to a file\n'
                             'D to set some failures\n'
                             'Q to quit\n')
                char = char.upper()
                if char == 'E':
                    cb = input('Enter the controller box name: ')
                    emissions = model.get_controller_box_emissions(cb)
                    for i in range(0, 3):
                        print('Row {}, {} - scfh'.format(i, emissions[i]))
                if char == 'Q':
                    StatisticsCollector.write_out_stats(Logger.get_dir()
                                                        + '/stats_' + time.strftime("%Y-%m-%d-%H:%M") + '.json')
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
                if char == 'S':
                    print(StatisticsCollector.get_stats())
                if char == 'G':
                    print('Saving graph...')
                    model.graph.save_graph(Logger.get_dir() + '/graph_' + time.strftime("%Y-%m-%d-%H:%M") + '.gml')
                    print('Graph saved')
                if char == 'D':
                    labjack_to_fail = input('Input the full name of the labjack to kill (ex: CB-1W.LJ-1): ').upper()
                    labjack_to_fail = labjacks.get(labjack_to_fail, False)
                    if not labjack_to_fail:
                        print('Not a valid labjack')
                        continue
                    type_of_failure = \
                        input('Type of failure? delay = D, stop-responding = S, '
                              'flaky = F, R = reset K = kill: ').upper()[0]
                    if type_of_failure == 'D':
                        print('Delaying {}'.format(labjack_to_fail))
                        delay = int(input('Input upper bound of delay (in whole # of ms): '))
                        labjack_to_fail.inject_failures({'delay-response': delay})
                    elif type_of_failure == 'S':
                        print('Stopping responses for {}'.format(labjack_to_fail))
                        labjack_to_fail.inject_failures({'stop-responding': True})
                    elif type_of_failure == 'F':
                        print('Delaying {}'.format(labjack_to_fail))
                        delay = int(input('Input upper bound of delay (in whole # of ms): '))
                        labjack_to_fail.inject_failures({'flake-response': delay})
                    elif type_of_failure == 'R':
                        print('Resetting {}'.format(labjack_to_fail))
                        labjack_to_fail.inject_failures({
                            'delay-response': False,
                            'stop-responding': False,
                            'flake-response': False
                        })
                    elif type_of_failure == 'K':
                        print('Killing {}'.format(labjack_to_fail))
                        labjack_to_fail.stop_server()
                if char == 'I':
                    remove_or_repair = input('- for remove, + for repair, | for repair all: ')
                    if remove_or_repair == '-':
                        u, v = input('Input the network link to remove as "<component-1> <component-2>": ').split()
                        network_model.disconnect_nodes(u, v)
                        print('Edge {} {} removed'.format(u, v))
                    elif remove_or_repair == '+':
                        u, v = input('Input the network link to repair as "<component-1> <component-2>": ').split()
                        network_model.repair_edge(u, v)
                        print('Edge {} {} repaired'.format(u, v))
                    elif remove_or_repair == '|':
                        network_model.reset_network()
                        print('Network nodes have been reset')
                if char == 'J':
                    u, v = input('Input the network link to check as "<component-1> <component-2>": ').split()
                    if network_model.network_connected(u, v):
                        print('Nodes are connected')
                    else:
                        print('Nodes are not connected')
            except Exception as e:
                print(e)
    except KeyboardInterrupt:
        print('Execution interrupted, exiting now...')
        StatisticsCollector.write_out_stats(Logger.get_dir()
                                            + '/stats_' + time.strftime("%Y-%m-%d-%H:%M") + '.json')
        for lj_thread in labjack_threads:
            lj_thread.stop()
        exit()

from metecmodel import Model
from labjackemulator import LabJack
from main_program.labjackthread import LabJackThread
if __name__ == '__main__':
    model = Model('../Resources/sensor_properties.csv', '../Resources/GSH-1-volumes.json')
    labjack = LabJack('CB-1W.LJ-1', '../Resources/pins_to_registers.csv',
                      '../Resources/sensor_properties.csv', model, 502)
    lj_thread = LabJackThread(labjack)
    lj_thread.start()
    while True:
        char = input('E for get emissions, Q for quit\n')
        if char == 'E':
            print(model.get_controller_box_emissions('CB-1W'))
        if char == 'Q':
            lj_thread.stop()
            lj_thread.join(5)
            exit()

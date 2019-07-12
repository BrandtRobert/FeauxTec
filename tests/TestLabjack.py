import unittest
from metecmodel import Model
from labjackemulator import LabJack
from main_program import LabJackThread
from pymodbus.client.sync import ModbusTcpClient


class TestLabjack(unittest.TestCase):

    model = Model('../Resources/sensor_properties.csv', '../Resources/GSH-1-volumes.json',
                  initial_pressure=50, initial_temperature=75)
    labjack = LabJack('CB-1W.LJ-1', '../Resources/pins_to_registers.csv', '../Resources/sensor_properties.csv',
                      model, 510)
    labjack_thread = LabJackThread(labjack)
    labjack_thread.start()
    modbus_client: ModbusTcpClient = ModbusTcpClient('localhost', 510)
    modbus_client.connect()

    @staticmethod
    def _convert_to_32_float(register1, register2) -> float:
        # Pad hex with 0's
        reg1_hex = hex(register1)[2:]
        if len(reg1_hex) < 4:
            reg1_hex = reg1_hex + ('0' * (4-len(reg1_hex)))
        reg2_hex = hex(register2)[2:]
        if len(reg2_hex) < 4:
            reg2_hex = reg2_hex + ('0' * (4-len(reg2_hex)))
        import struct
        hex_bytes = reg1_hex + reg2_hex
        f = struct.unpack('!f', bytes.fromhex(hex_bytes))
        return f[0]


    '''
        Read PT-1, and TC-1 from the labjack
            * PT-1 : register 0
            * TC-1 : register 4
    '''
    def test_read_sensor(self):
        registers_pt1 = self.modbus_client.read_input_registers(0, 2)
        reg1, reg2 = registers_pt1.registers
        reading = self._convert_to_32_float(reg1, reg2)
        # apply transformation to reading
        self.assertAlmostEqual(50, reading * 50 - 10.3, places=5)
        registers_tc1 = self.modbus_client.read_input_registers(4, 2)
        reg1, reg2 = registers_tc1.registers
        reading = self._convert_to_32_float(reg1, reg2)
        self.assertAlmostEqual(75, reading, places=5)

    '''
        Test bulk register read
    '''
    def test_read_sensors(self):
        holding_registers = self.modbus_client.read_holding_registers(0, 6)
        pt_1, pt_2, _, _, tc_1, tc_2 = holding_registers.registers
        pt_reading = self._convert_to_32_float(pt_1, pt_2) * 50 - 10.3
        tc_reading = self._convert_to_32_float(tc_1, tc_2)
        self.assertAlmostEqual(50, pt_reading, places=5)
        self.assertAlmostEqual(75, tc_reading, places=5)

    '''
        Test write single valve
    '''
    def test_write_single_valve(self):
        response = self.modbus_client.write_register(2017, 0)
        self.assertTrue(1, response.value)
        self.assertTrue(2017, response.address)
        self.modbus_client.write_register(2017, 1)

    def test_write_three_way_valve(self):
        response = self.modbus_client.write_register(2016, 0)
        self.assertTrue(1, response.value)
        self.assertTrue(2016, response.address)
        self.modbus_client.write_register(2016, 1)

    def test_write_multiple_valves(self):
        response = self.modbus_client.write_registers(2016, [0, 0, 0, 0])
        self.assertTrue(4, response.count)
        self.assertTrue(2016, response.address)
        self.modbus_client.write_registers(2016, [1, 1, 1, 1])

    def test_read_dio_state(self):
        self.modbus_client.write_registers(2016, [0, 0, 0, 0])
        expected_bin = '0xfff0ffff'
        response = self.modbus_client.read_input_registers(2800, 2)
        register1, register2 = response.registers
        hex_str = hex(register1) + hex(register2)[2:]
        self.assertEqual(expected_bin, hex_str)
        self.modbus_client.write_registers(2016, [1, 1, 1, 1])

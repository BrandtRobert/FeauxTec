import socket
import unittest
from modbushandler import ModbusReceiver
from pymodbus.client.sync import ModbusTcpClient
import threading


class TestModbusReceiver(unittest.TestCase):

    def setUp(self) -> None:
        self.slave = ModbusReceiver(8080)
        self.data = {}

        def callback(data):
            print(data)
            self.data = data
        self.callback = callback

        self.thread = threading.Thread(target=ModbusReceiver.start_server, args=(self.slave, self.callback))
        self.thread.start()
        self.client: ModbusTcpClient = ModbusTcpClient('localhost', 8080)
        self.client.connect()

    def tearDown(self) -> None:
        # set stop flag
        self.slave.stop_server()
        self.thread.join()
        self.client.close()

    def test_read_coils(self):
        self.client.read_coils(0, 2)
        self.assertEqual(self.data['address'], 0, 'Start coil read request for register 0')
        self.assertEqual(self.data['count'], 2, 'Should read two coils')
        self.assertEqual(self.data['function_code'], 1, 'read_coil should be function code 1')

    def test_read_discrete_inputs(self):
        self.client.read_discrete_inputs(1000, 4)
        self.assertEqual(self.data['address'], 1000, 'Starting read address should be 1000')
        self.assertEqual(self.data['count'], 4, 'Number of discrete inputs should be 4')
        self.assertEqual(self.data['function_code'], 2, 'read_discrete_inputs should be function code 2')

    def test_read_holding_registers(self):
        self.client.read_holding_registers(2000, 8)
        self.assertEqual(self.data['address'], 2000, 'Starting read address should be 2000')
        self.assertEqual(self.data['count'], 8, 'Number of read registers should be 8')
        self.assertEqual(self.data['function_code'], 3, 'read_holding_registers should be function code 3')

    def test_read_input_registers(self):
        self.client.read_input_registers(4000, 4)
        self.assertEqual(self.data['address'], 4000, 'Starting read address should be 4000')
        self.assertEqual(self.data['count'], 4, 'Number of read registers should be 4')
        self.assertEqual(self.data['function_code'], 4, 'read_input_registers should be function code 4')

    def test_write_single_coil(self):
        self.client.write_coil(10000, 0xFF00)
        self.assertEqual(self.data['address'], 10000, 'Coil address should be 10,000')
        self.assertEqual(self.data['value'], 0XFF00, 'Write of 0xFF00 should turn switch on')
        self.assertEqual(self.data['function_code'], 5, 'write_single_coil should be function code 5')

    def test_write_single_holding_register(self):
        self.client.write_register(3000, 50)
        self.assertEqual(self.data['address'], 3000, 'register address should be 3000')
        self.assertEqual(self.data['value'], 50, 'written value should be 50')
        self.assertEqual(self.data['function_code'], 6, 'write_single_register should be function code 6')

    def test_write_multiple_coils(self):
        coil_vals = [0xFF00, 0, 0, 0xFF00, 0, 0, 0, 0xFF00, 0xFF00, 0xFF00, 0, 0xFF00]
        self.client.write_coils(0x1000, coil_vals)
        self.assertEqual(self.data['address'], 0x1000, 'Address should come back as 0x1000')
        self.assertListEqual(self.data['values'], coil_vals, 'Coil values set to 0xFF00 for on')
        self.assertEqual(self.data['function_code'], 15, 'function code should be 15')

    def test_write_multiple_holding_registers(self):
        register_vals = [2, 4, 6, 100]
        self.client.write_registers(6000, register_vals)
        self.assertEqual(self.data['address'], 6000, 'start register should be 6000')
        self.assertListEqual(self.data['values'], register_vals, 'Write values should match up to read values')
        self.assertEqual(self.data['count'], len(register_vals), 'Num registers should match up to list len')
        self.assertEqual(self.data['function_code'], 16, 'function code should be 16')

    def test_invalid_function_code(self):
        self.client.read_input_registers(0, 2)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('localhost', 8080))
            s.sendall(b'\x00\x01\x00\x00\x00\x02\x00\x17')
            response = s.recv(2)
            self.assertEqual(b'\x97\x01', response, 'Error codes should match up')
            s.close()
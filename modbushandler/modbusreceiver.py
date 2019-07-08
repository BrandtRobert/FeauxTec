import socket
from typing import Callable
from ModbusHandler import ModbusDecoder
import threading
from typing import Dict


class ModbusReceiver:

    def __init__(self, port, localhost=True):
        self.port = port
        self.localhost = localhost
        self.stop = threading.Event()

    '''
        Dispatches packet data for decoding based on it's function code.
        ModbusDecoder handles decoding of the packets and returns a Dict containing
        appropriate data. Invalid function codes lead to an invalid_function_code message which
        is also created by the modbus decoder.
    '''
    @staticmethod
    def _dissect_packet(packet_data) -> Dict:
        function_code = packet_data[0]
        switch = {
            1: ModbusDecoder.read_coils,
            2: ModbusDecoder.read_discrete_inputs,
            3: ModbusDecoder.read_holding_registers,
            4: ModbusDecoder.read_input_registers,
            5: ModbusDecoder.write_single_coil,
            6: ModbusDecoder.write_single_holding_register,
            15: ModbusDecoder.write_multiple_coils,
            16: ModbusDecoder.write_multiple_holding_registers
        }
        function = switch.get(function_code, ModbusDecoder.invalid_function_code)
        return function(packet_data)

    '''
        Starts the Modbus server and listens for packets over a TCP/IP connection. By default it will bind to
        localhost at a port specified in the constructor. Upon receiving a modbus message it will decode the header
        and send the function code and data to the _dissect_packet function for further processing. Error packets
        lead to an immediate response with an error code, while valid requests are sent back to the request handler.
    '''
    def start_server(self, request_handler: Callable) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if self.localhost:
                s.bind(('localhost', self.port))
            else:
                s.bind((socket.gethostname(), self.port))
            s.listen(5)
            print('Starting server at {}:{}'.format(socket.gethostname(), self.port))
            while not self.stop.is_set():
                connection, address = s.accept()
                with connection:
                    header = connection.recv(7)
                    if header == b'' or len(header) <= 0:
                        continue
                    # Modbus length is in bytes 4 & 5 of the header according to spec (pg 25)
                    # https://www.prosoft-technology.com/kb/assets/intro_modbustcp.pdf
                    length = (header[4] << 8) | (header[5])
                    if length == 0:
                        continue
                    data = connection.recv(length)
                    is_error, dissection = self._dissect_packet(data)
                    if is_error:
                        connection.sendall(dissection)
                        connection.close()
                        continue
                    else:
                        dissection['type'] = 'request'
                        dissection['function_code'] = data[0]
                        request_handler(dissection)
                        # response = request_handler(dissection)
                        # connection.sendall(response)
                        connection.close()

    '''
        Breaks the server out of it's blocking accept call and sets the stop flag.
        In order to do this the method uses a 'dummy' connection to break the blocking call.
        It then sends a 'dummy' message that will lead to the method dropping the request and exiting.
        **NOTE**: This is especially useful when the server is being run on it's own thread.
    '''
    def stop_server(self) -> None:
        self.stop.set()
        # In order to stop the server we have to interrupt
        # The blocking socket.accept()
        # We create a connection that sends a header for a 0 length
        # Packet
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('localhost', self.port))
            s.sendall(b'\x00\x01\x00\x00\x00\x00\x00')
            s.close()


if __name__ == '__main__':
    m = ModbusReceiver(8080)

    def handler(msg):
        print(msg)
    m.start_server(handler)

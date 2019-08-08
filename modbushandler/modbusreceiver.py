import socket
import time
from typing import Callable
from modbushandler import modbusdecoder
import threading
from typing import Dict
from logger import Logger
from time import sleep
from modbushandler.util import stringify_bytes
from metecmodel import StatisticsCollector


class ModbusReceiver:

    def __init__(self, port, localhost=True, device_function_codes=None, socket_type=socket.SOCK_STREAM):
        self.port = port
        self.localhost = localhost
        self.stop = threading.Event()
        self.done = threading.Event()
        self.device_function_codes = device_function_codes
        self.logger = Logger('ServerLogger-{}'.format(port), '../logger/logs/server_log.txt', prefix='Server {}'.format(port))
        self._current_connection = None
        self.socket_type = socket_type

    '''
        Dispatches packet data for decoding based on it's function code.
        ModbusDecoder handles decoding of the packets and returns a Dict containing
        appropriate data. Invalid function codes lead to an invalid_function_code message which
        is also created by the modbus decoder.
    '''
    def _dissect_packet(self, packet_data) -> Dict:
        function_code = packet_data[0]
        # Check that the device supports this function code
        if self.device_function_codes:
            if function_code not in self.device_function_codes:
                return modbusdecoder.invalid_function_code(packet_data)
        switch = {
            1: modbusdecoder.read_coils,
            2: modbusdecoder.read_discrete_inputs,
            3: modbusdecoder.read_holding_registers,
            4: modbusdecoder.read_input_registers,
            5: modbusdecoder.write_single_coil,
            6: modbusdecoder.write_single_holding_register,
            15: modbusdecoder.write_multiple_coils,
            16: modbusdecoder.write_multiple_holding_registers
        }
        function = switch.get(function_code, modbusdecoder.invalid_function_code)
        return function(packet_data)

    def _start_server_tcp(self, request_handler: Callable) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if self.localhost:
                s.bind(('localhost', self.port))
            else:
                s.bind((socket.gethostname(), self.port))
            s.listen(5)
            self.logger.info('Server started {}:{}'.format(socket.gethostname(), self.port))
            while not self.stop.is_set():
                self._current_connection, address = s.accept()
                self.logger.info('New connection accepted {}'.format(self._current_connection.getpeername()))
                with self._current_connection:
                    while not self.stop.is_set():
                        try:
                            buffer = self._current_connection.recv(7)
                            if buffer == b'' or len(buffer) <= 0:
                                self.logger.debug('Initial read was empty, peer connection was likely closed')
                                break
                            header = buffer
                            self.logger.debug('MB:{} Header DATA like: {}'.format(self.port, header))
                            # Modbus length is in bytes 4 & 5 of the header according to spec (pg 25)
                            # https://www.prosoft-technology.com/kb/assets/intro_modbustcp.pdf
                            header = modbusdecoder.dissect_header(header)
                            length = header['length']
                            if length == 0:
                                self.logger.debug('A length 0 header was read, closing connection')
                                break
                            data = self._current_connection.recv(length-1)
                            StatisticsCollector.increment_packets_received()
                            response_start = time.time()
                            is_error, dissection = self._dissect_packet(data)
                            if is_error:
                                self.logger.debug('MB:{} Header appears like: {}'.format(self.port, header))
                                self.logger.debug(
                                    'MB:{} Request: {}'.format(self.port, stringify_bytes(buffer + data)))
                                self.logger.debug(
                                    'MB:{} An error was found in the modbus request {}'.format(self.port, stringify_bytes(dissection)))
                                self._current_connection.sendall(dissection)
                                response_stop = time.time()
                                StatisticsCollector.increment_error_packets_sent()
                                StatisticsCollector.increment_responses_sent()
                                StatisticsCollector.increment_avg_response(response_stop - response_start)
                                continue
                            else:
                                dissection['type'] = 'request'
                                header['function_code'] = data[0]
                                response = request_handler({
                                    'header': header,
                                    'body': dissection
                                })
                                self.logger.debug(
                                    'MB:{} Header: {} Body:{}'.format(self.port, header, dissection))
                                self.logger.debug(
                                    'MB:{} Request: {}'.format(self.port, stringify_bytes(buffer + data)))
                                self.logger.debug('MB:{} Responding: {}'.format(self.port, stringify_bytes(response)))
                                self._current_connection.sendall(response)
                                response_stop = time.time()
                                StatisticsCollector.increment_responses_sent()
                                StatisticsCollector.increment_avg_response(response_stop - response_start)
                        except IOError as e:
                            self.logger.warning('An IO error occurred when reading the socket {}'.format(e))
                            self.logger.debug('Closing connection')
                            self._current_connection.close()
                            StatisticsCollector.increment_socket_errors()
                            break
            self.done.set()

    def _start_server_udp(self, request_handler: Callable) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if self.localhost:
                s.bind(('localhost', self.port))
                self.logger.info('Starting UDP server at localhost:{}'.format(self.port))
            else:
                s.bind((socket.gethostname(), self.port))
                self.logger.debug('Starting UDP server at {}:{}'.format(socket.gethostname(), self.port))
            while not self.stop.is_set():
                try:
                    buffer, address = s.recvfrom(256)
                    self.logger.info('Message received from: {}'.format(address))
                    StatisticsCollector.increment_packets_received()
                    response_start = time.time()
                    if buffer == b'' or len(buffer) <= 0:
                        self.logger.debug('Initial read was empty, peer connection was likely closed')
                        continue
                    header = buffer[:7]
                    header = modbusdecoder.dissect_header(header)
                    length = header['length']
                    if length == 0:
                        self.logger.debug('Length 0 message received')
                        continue
                    data = buffer[7: 7 + length - 1]
                    is_error, dissection = self._dissect_packet(data)
                    if is_error:
                        self.logger.debug('An error was found in the modbus request {}'.format(dissection))
                        self.logger.debug('Header appears like: {}'.format(header))
                        self.logger.debug('Buffer: {}'.format(stringify_bytes(buffer)))
                        s.sendto(dissection, address)
                        response_stop = time.time()
                        StatisticsCollector.increment_avg_response(response_stop - response_start)
                        StatisticsCollector.increment_error_packets_sent()
                        StatisticsCollector.increment_responses_sent()
                        continue
                    else:
                        dissection['type'] = 'request'
                        header['function_code'] = data[0]
                        response = request_handler({
                            'header': header,
                            'body': dissection
                        })
                        s.sendto(response, address)
                        response_stop = time.time()
                        StatisticsCollector.increment_avg_response(response_stop - response_start)
                        StatisticsCollector.increment_responses_sent()
                        self.logger.debug('MB:{} Request: {}'.format(self.port, stringify_bytes(buffer[:7+length])))
                        self.logger.debug('MB:{} Header: {} Body:{}'.format(self.port, header, dissection))
                        self.logger.debug('MB:{} Responding: {}'.format(self.port, stringify_bytes(response)))
                except IOError as e:
                    self.logger.warning('An IO error occurred with the socket {}'.format(e))
                    StatisticsCollector.increment_socket_errors()
                    continue
        self.done.set()
    '''
        Starts the Modbus server and listens for packets over a TCP/IP connection. By default it will bind to
        localhost at a port specified in the constructor. Upon receiving a modbus message it will decode the header
        and send the function code and data to the _dissect_packet function for further processing. Error packets
        lead to an immediate response with an error code, while valid requests are sent back to the request handler.
    '''
    def start_server(self, request_handler: Callable) -> None:
        if self.socket_type == socket.SOCK_STREAM:
            self._start_server_tcp(request_handler)
        else:
            self._start_server_udp(request_handler)

    '''
        Breaks the server out of it's blocking accept or recv calls and sets the stop flag.
        In order to do this the method uses a 'dummy' connection to break the blocking call.
        It then sends a 'dummy' message that will lead to the method dropping the request and exiting.
        **NOTE**: This is especially useful when the server is being run on it's own thread.
    '''
    def stop_server(self) -> None:
        self.logger.info('Stopping server now')
        self.stop.set()
        if self._current_connection:
            self._current_connection.close()
        sleep(.5)
        # In order to stop the server we have to interrupt
        # The blocking socket.accept()
        # We create a connection that sends a header for a 0 length
        # Packet
        if not self.done.is_set() and self.socket_type == socket.SOCK_STREAM:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if self.localhost:
                    s.connect(('localhost', self.port))
                else:
                    s.connect((socket.gethostname(), self.port))
                s.sendall(b'\x00\x01\x00\x00\x00\x00\x00')
                s.close()


if __name__ == '__main__':
    m = ModbusReceiver(8080, socket_type=socket.SOCK_DGRAM)
    def handler(msg):
        print(msg)
        return b'received'
    m.start_server(handler)

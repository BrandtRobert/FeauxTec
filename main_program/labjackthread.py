from threading import Thread


class LabJackThread(Thread):

    def __init__(self, labjack):
        Thread.__init__(self)
        self.labjack = labjack
        self.daemon = True

    def run(self):
        self.labjack.start_server()

    def stop(self):
        self.labjack.stop_server()

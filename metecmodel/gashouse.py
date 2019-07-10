from metecmodel import ControllerBox


class GasHouse:

    def __init__(self, name: str):
        self.name = name
        self.controller_boxes = {}

    def add_controller_box(self, box: ControllerBox):
        self.controller_boxes[box.get_name()] = box

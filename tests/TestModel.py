import unittest
from metecmodel import Model


class TestModel(unittest.TestCase):

    model = Model('../Resources/sensor_properties.csv', '../Resources/GSH-1-volumes.json', initial_pressure=50)

    def setUp(self) -> None:
        self.model.change_model_pressure(50)
        self.model.change_model_temperature(75)
        self.model.set_valve('CB-1W.EV-11', 'closed')
        self.model.set_valve('CB-1W.EV-22', 'closed')
        self.model.set_valve('CB-1W.EV-33', 'closed')

    def test_get_component(self):
        component = self.model.get_component('CB-1W.PT-1')
        self.assertEqual(component.get_type(), 'PressureTransducer')
        self.assertEqual(component.get_reading(), 50)

    def test_get_component_bad(self):
        self.assertRaises(KeyError, self.model.get_component, 'SNAKE')

    def test_set_valve(self):
        self.model.set_valve('CB-1T.EV-11', 'open')
        component = self.model.get_component('CB-1T.EV-11')
        self.assertEqual(component.get_reading(), 'open')

    def test_get_controller_box_emissions(self):
        self.model.set_valve('CB-1W.EV-11', 'open')
        self.model.set_valve('CB-1W.EV-22', 'open')
        self.model.set_valve('CB-1W.EV-33', 'open')
        emissions = self.model.get_controller_box_emissions('CB-1W')
        expected = [2.7, 11, 33]
        self.assertEqual(expected, emissions)

    def test_calculate_flows(self):
        self.model.set_valve('CB-1W.EV-11', 'open')
        self.model.set_valve('CB-1W.EV-22', 'open')
        self.model.set_valve('CB-1W.EV-33', 'open')
        expected = sum([2.7, 11, 33]) * .47
        self.assertEqual(expected, self.model.calculate_flows('GSH-1')['GSH-1.FM-1'])

    def test_change_model_pressure(self):
        self.model.change_model_pressure(20)
        self.model.set_valve('CB-1W.EV-11', 'open')
        self.model.set_valve('CB-1W.EV-22', 'open')
        self.model.set_valve('CB-1W.EV-33', 'open')
        expected_flow = sum([1.4, 6.1, 17]) * .47
        reading = self.model.get_component('CB-1W.PT-1').get_reading()
        self.assertEqual(expected_flow, self.model.calculate_flows('GSH-1')['GSH-1.FM-1'])
        self.assertEqual(20, reading)
        self.assertEqual(20, self.model.initial_pressure)

    def test_change_model_temperature(self):
        self.model.change_model_temperature(100)
        component = self.model.get_component('CB-2S.TC-1')
        self.assertEqual(100, component.get_reading())
        self.assertEqual(100, self.model.initial_temperature)

    def test_are_connected(self):
        self.assertTrue(self.model.are_connected('GSH-1.VOL-16', 'CB-1W.VOL-1'))
        self.assertFalse(self.model.are_connected('GSH-1.VOL-16', 'CB-1W.VOL-5'))
        self.model.set_valve('CB-1W.EV-22', 'open')
        self.assertTrue(self.model.are_connected('GSH-1.VOL-16', 'CB-1W.VOL-5'))

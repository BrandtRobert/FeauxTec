import unittest
from metecmodel import Model


class TestEmissions(unittest.TestCase):

    model = Model('../Resources/sensor_properties.csv', '../Resources/GSH-1-volumes.json')

    def test_emissions_normal(self):
        self.model.set_valve('CB-1W.EV-12', 'open')
        self.model.set_valve('CB-1W.EV-13', 'open')
        self.model.change_model_pressure(50)
        emissions = self.model.get_controller_box_emissions('CB-1W')
        expected = [17, 0, 0]
        self.assertEqual(expected, emissions)
        self.model.set_valve('CB-1W.EV-12', 'closed')
        self.model.set_valve('CB-1W.EV-13', 'closed')

    def test_emissions_normal_interpolate(self):
        self.model.set_valve('CB-1W.EV-12', 'open')
        self.model.change_model_pressure(15)
        emissions = self.model.get_controller_box_emissions('CB-1W')
        expected = [2.45, 0, 0]
        self.assertEqual(expected, emissions)
        self.model.set_valve('CB-1W.EV-12', 'closed')

    def test_flows(self):
        self.model.change_model_pressure(100)
        self.model.set_valve('CB-1W.EV-12', 'open')
        self.model.set_valve('CB-1W.EV-13', 'open')
        self.model.set_valve('CB-1T.EV-22', 'open')
        self.model.set_valve('CB-1T.EV-24', 'open')
        flows = self.model.calculate_flows('GSH-1')
        expected = 67.21
        self.assertEqual(expected, flows['GSH-1.FM-1'])
        self.model.set_valve('CB-1W.EV-12', 'closed')
        self.model.set_valve('CB-1W.EV-13', 'closed')
        self.model.set_valve('CB-1T.EV-22', 'closed')
        self.model.set_valve('CB-1T.EV-24', 'closed')

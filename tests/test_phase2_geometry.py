"""Geometry checks on deliberately ambiguous paths, independent of the Rome data."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('phase2_geometry',
        Path(__file__).resolve().parents[1] / 'scripts/prepare_shared_geometry.py')
geometry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geometry)


class GeometryTests(unittest.TestCase):
    def test_project_and_clip_stops_inside_shape_edges(self):
        line = [(0., 0.), (100., 0.), (200., 0.)]
        cumulative, anchors = geometry.anchors(line, [(25., 5.), (175., -3.)])
        self.assertAlmostEqual(anchors[0][0], 25.)
        self.assertAlmostEqual(anchors[1][0], 175.)
        self.assertAlmostEqual(anchors[0][1], 5.)
        samples = geometry.sample_segment(line, cumulative, anchors[0][0], anchors[1][0])
        self.assertEqual(samples[0], (25., 0.))
        self.assertEqual(samples[-1], (175., 0.))

    def test_same_endpoints_do_not_prove_same_path(self):
        line = [(float(i), 0.) for i in range(101)]
        detour = [(float(i), 40.*(1.-abs(i-50)/50.)) for i in range(101)]
        a = {'samples': line, 'length_m': 100.}
        b = {'samples': detour, 'length_m': 100.}  # Isolate the shape-deviation test.
        self.assertFalse(geometry.equivalent(a, b))

    def test_direction_and_length_are_checked(self):
        line = [(float(i), 0.) for i in range(101)]
        a = {'samples': line, 'length_m': 100.}
        self.assertFalse(geometry.equivalent(a, {'samples': list(reversed(line)), 'length_m': 100.}))
        self.assertFalse(geometry.equivalent(a, {'samples': line, 'length_m': 120.}))
        self.assertTrue(geometry.equivalent(a, {'samples': [(x, 5.) for x, _ in line], 'length_m': 100.}))


if __name__ == '__main__':
    unittest.main()

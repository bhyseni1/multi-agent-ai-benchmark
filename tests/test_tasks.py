import unittest
from benchmark.run import tasks, answer
class TestBenchmark(unittest.TestCase):
    def test_reproducible(self):
        self.assertEqual(tasks(10,42),tasks(10,42))
    def test_answers(self):
        self.assertEqual(answer('Reasoning\nANSWER: -123'),-123)
        self.assertIsNone(answer('No numeric final answer'))
    def test_unique_ids(self):
        self.assertEqual(len({x['task_id'] for x in tasks(30,42)}),30)
if __name__=='__main__': unittest.main()

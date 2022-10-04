import unittest
from  historical_data_feeds.historical_data_feeds import HistoricalDataFeeds

class TestConfig:
    name = "test",
    strategy_path = 'hackaton1'

class TestHistoricalDataFeeds(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        print('setup class')

    @classmethod
    def tearDownClass(cls) -> None:
        print('teardown class')

    def setUp(self) -> None:

        config = TestConfig()
        self.historical_data_feeds = HistoricalDataFeeds(config)
        

    def tearDown(self) -> None:
        return super().tearDown()

    def test_get_next_value(self):
        result = self.historical_data_feeds.get_next_value()
        self.assertEqual(result, False)



if __name__ == '__main__':
    unittest.main()

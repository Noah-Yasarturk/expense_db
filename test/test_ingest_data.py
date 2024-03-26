import unittest
import os 
import sys 
sys.path.append(os.getcwd() + '/parse/')
import ingest_data


class TestIngestData(unittest.TestCase):


    def test_no_number_sign(self):
        ''' Number sign # should never be returned as an amt '''
        line = '12/14     WENDYS #3830 ATLANTA GA 11.21\n'
        amt = ingest_data.get_transaction_amount(line)
        self.assertTrue(isinstance(amt, float), f'Amount not returned as a float: {amt}') 


if __name__ == "__main__":
    unittest.main()
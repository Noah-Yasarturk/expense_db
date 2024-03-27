import unittest
import os 
import sys 
sys.path.append(os.getcwd() + '/extract/')
import ingest_data
import hidden_test_constants

class TestIngestData(unittest.TestCase):

    def test_get_purchases_this_period(self):
        ''' We should be able to extract the total purchases for a given period from the statement page '''
        purch_amt = ingest_data.get_purchases_this_period(hidden_test_constants.pg_smp_1)
        self.assertTrue(purch_amt == 2435.96, f"Failed to get proper purchase amount: {purch_amt}")


    def test_get_open_cls(self):
        ''' We should be able to extract the opening & closing date from the statement page '''
        open_dt, close_dt = ingest_data.get_opening_closing_date(hidden_test_constants.pg_smp_1)
        self.assertTrue(open_dt.year == 2021 and close_dt.month == 1)


    def test_no_number_sign(self):
        ''' Number sign # should never be returned as an amt '''
        line = '12/14     WENDYS #3830 ATLANTA GA 11.21\n'
        amt = ingest_data.get_transaction_amount(line)
        self.assertTrue(isinstance(amt, float), f'Amount not returned as a float: {amt}') 


if __name__ == "__main__":
    unittest.main()
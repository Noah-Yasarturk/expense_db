''' Go through the transactions and apply labels based on their descriptions '''
import os 
import sys 
import pandas as pd
sys.path.append(os.getcwd() + 'src/extract/')
from ingest_data import ALL_TRANSACTIONS_OUTPUT_PATH



if __name__ == "__main__":
    trans_df = pd.read_csv(ALL_TRANSACTIONS_OUTPUT_PATH)
    print()
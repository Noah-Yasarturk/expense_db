''' Go through the transactions and apply labels based on their descriptions '''
import os 
import sys 
import pandas as pd
import json
import re
sys.path.append(os.getcwd() + '/src/')
import utils
sys.path += [utils.EXTRACT_FOLDER]
from utils import set_logger, TRANSFORM_FOLDER
from ingest_data import ALL_TRANSACTIONS_OUTPUT_PATH

TRANS_CATEGORY_MAP_JSON = TRANSFORM_FOLDER + 'trans_desc_cat_map.json'


def apply_category(desc: str, cat_map: dict) -> str:
    ''' Apply the proper category to the transaction description '''
    for category, desc_match_list in cat_map.items(): 
        for desc_match in desc_match_list: 
            if desc_match in desc:
                return category
    return None


def categorize_transactions(cat_map: dict, trans_df: pd.DataFrame) -> pd.DataFrame:
    ''' Apply transaction category from `cat_map` & raise Exception if none match '''
    trans_cats_l = []
    for dt in trans_df['Opening Date'].unique():
        trans_this_period_df = trans_df.loc[trans_df['Opening Date'] == dt]
        for _, row in trans_this_period_df.iterrows():
            desc = row['Description'].upper()
            desc = re.sub('\s+', ' ', desc)
            d = {col: row[col] for col in trans_df.columns}
            d['Category'] = None
            if d['Purchase Amount'] != 0:
                d['Category'] = apply_category(desc, cat_map)
            trans_cats_l.append(d)
    trans_cats_df = pd.DataFrame(trans_cats_l)
    return trans_cats_df


if __name__ == "__main__":
    set_logger(TRANSFORM_FOLDER + 'label_transactions.log')
    trans_df = pd.read_csv(ALL_TRANSACTIONS_OUTPUT_PATH)
    cat_map = json.load(open(TRANS_CATEGORY_MAP_JSON))
    trans_cats_df = categorize_transactions(cat_map, trans_df)
    num_transactions = trans_cats_df[(trans_cats_df['Purchase Amount'] > 0)].shape[0]
    num_categorized_line_items = trans_cats_df[(trans_cats_df['Category'].isnull() == False)].shape[0]
    assert num_transactions == num_categorized_line_items
    trans_cats_df.to_csv(TRANSFORM_FOLDER + 'cat_trans.csv', index=False)
            
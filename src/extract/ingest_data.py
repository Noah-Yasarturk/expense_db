''' Grab Chase credit card transactions from my local folder and extract the needed data '''
from pypdf import PdfReader
import os 
import sys
import logging
import pandas as pd
import re
from datetime import datetime
sys.path.append(os.getcwd())
from src.utils import set_logger, EXTRACT_FOLDER

logger = logging.getLogger()

LOG_PATH = EXTRACT_FOLDER + "ingest_data.log"
PDF_PATH = r'C:\Users\NoahY\OneDrive\Documents\Finances\Banking\Chase Statements\Credit Card statements\2024.03.25'
PDF_DIR = os.path.normpath(PDF_PATH)
CHASE_HEADERS = ["Date of\nTransaction", "Merchant Name or Transaction Description","$ Amount"]
ALL_TRANSACTIONS_OUTPUT_PATH = EXTRACT_FOLDER+ 'all_transactions.csv'


def get_transaction_date(txt_line: str) -> str:
    ''' Pull date of the transaction from the line item '''
    trans_date_mtch = re.match('([0-9]{2}\/[0-9]{2})', txt_line, flags=re.IGNORECASE)
    if not trans_date_mtch:
        return None
    trans_date_grps = trans_date_mtch.groups()
    trans_date = trans_date_grps[0]
    return trans_date


def get_transaction_amount(txt_line: str) -> float:
    '''Pull transaction amount from the line item '''
    amt = None
    amt_mtchs = re.findall('\s+(-*[0-9]*,*[0-9]*.[0-9]{2})\n*', txt_line) 
    for m in amt_mtchs:
        amt = m.replace(',','')
    return float(amt)


def trans_text_to_df(txt: str) -> pd.DataFrame:
    ''' Take transaction text and convert it to a DataFrame of transactions '''
    txt_lines = txt.split('\n')
    l = []
    for line in txt_lines:
        if line:
            trans_date = get_transaction_date(line)
            if not trans_date:
                continue
            amt = get_transaction_amount(line)
            desc = line.split(trans_date)[1].split(str(amt))[0].strip()
            not_interest_line_item = 'PURCHASE INTEREST' not in desc
            if not_interest_line_item and amt > 0:
                l.append({
                    'Transaction Date': trans_date,
                    'Purchase Amount': amt,
                    'Payment Amount': 0,
                    'Interest Amount': 0,
                    'Description': desc
                })
            elif not_interest_line_item and amt < 0:
                l.append({
                    'Transaction Date': trans_date,
                    'Purchase Amount': 0,
                    'Payment Amount': amt * -1,
                    'Interest Amount': 0, 
                    'Description': desc
                })
            else:
                 l.append({
                        'Transaction Date': trans_date,
                        'Purchase Amount': 0,
                        'Payment Amount': 0,
                        'Interest Amount': amt, 
                        'Description': desc
                    })
    return pd.DataFrame(l)


def get_opening_closing_date(page: str) -> tuple[datetime, datetime]:
    ''' If the page has the opening & closing date of the statement, extract it '''
    page_lines = page.split('\n')
    m = 'Opening/Closing Date'
    for ln in page_lines:
        if m in ln: 
            rng_txt = ln.split(m)[1].strip()
            [open_dt_str, close_dt_str] = [t.strip() for t in rng_txt.split('-')]
            opening_date = datetime.strptime(open_dt_str, '%m/%d/%y')
            closing_date = datetime.strptime(close_dt_str, '%m/%d/%y')
            return opening_date, closing_date
    return None, None


def get_purchases_this_period(page: str) -> float:
    ''' Pull total purchase amount from text if it exists '''
    page_lines = page.split('\n')
    m = 'Purchases +$'
    for ln in page_lines:
        if m in ln:
            purch_amt = float(ln.split(m)[1].replace(',',''))
            return purch_amt
    return None


def get_pdf_data(pdf_dir:str=PDF_DIR) -> list[pd.DataFrame]:
    ''' Grab all pdfs from `PDF_DIR` and extract transaction data '''
    pdf_data: list[pd.DataFrame] = []
    for filename in os.listdir(pdf_dir):
        logger.info(f'## Processing {filename} ##')
        reader = PdfReader(pdf_dir + '\\' + filename)
        number_of_pages = len(reader.pages)
        found_transaction_table = False
        transaction_table_text = ''
        open_dt, close_dt = None, None
        purchases_this_period = None
        for pg_num in range(0, number_of_pages):
            page = reader.pages[pg_num]
            text = page.extract_text()
            logger.info(text)
            if not open_dt and not close_dt:
                open_dt, close_dt = get_opening_closing_date(text)
            if not purchases_this_period:
                purchases_this_period = round(get_purchases_this_period(text), 2)
            # Get transaction table
            if CHASE_HEADERS[0] in text:
                found_transaction_table = True 
                # Transaction table is from "$ Amount" to 'Total fees charged'
                this_pg_transaction_tbl = text.split(CHASE_HEADERS[-1])[1]
                this_pg_transaction_tbl = this_pg_transaction_tbl.split('Total fees charged')[0]
                # Sometimes the table goes into a new page, in which case "PAYMENTS AND OTHER CREDITS" is on the first
                transaction_table_text += this_pg_transaction_tbl.split('PAYMENTS AND OTHER CREDITS')[0]
        # Convert table text into DataFrame
        transaction_df = trans_text_to_df(transaction_table_text)
        transaction_df['Opening Date'] = open_dt
        transaction_df['Closing Date'] = close_dt
        transaction_df['Purchases this Period'] = purchases_this_period
        sum_of_parsed_transactions = round(transaction_df['Purchase Amount'].sum(), 2)
        try:
            assert purchases_this_period == sum_of_parsed_transactions
        except AssertionError as e: 
            logger.error(e)
            err = f"Total purchases parsed did not equal sum of purchases for {filename}.\n"
            err += f"Parsed purchase amount: {sum_of_parsed_transactions}\n"
            err += f"Sum of parsed transactions amount: {purchases_this_period}"
            raise Exception(err)
        logger.info(transaction_df)
        pdf_data.append(transaction_df)
        logger.info(f'## Done with {filename} ##')
        if not found_transaction_table:
            m = f"Couldnt find table in {filename}"
            raise Exception(m)
    return pdf_data


if __name__ == "__main__":
    set_logger(LOG_PATH)
    pdf_data = get_pdf_data()
    pdf_data_concat_df = pd.concat(pdf_data)
    # For now, just output as a csv 
    logger.info(f"Outputting all transactions as csv at {ALL_TRANSACTIONS_OUTPUT_PATH}")
    pdf_data_concat_df.to_csv(ALL_TRANSACTIONS_OUTPUT_PATH)
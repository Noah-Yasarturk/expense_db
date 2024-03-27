from pypdf import PdfReader
import os 
import logging
import sys 
import pandas as pd
import re
from datetime import datetime

logger = logging.getLogger()

PATH = r'C:\Users\NoahY\OneDrive\Documents\Finances\Banking\Chase Statements\Credit Card statements\2024.03.25'
PDF_DIR = os.path.normpath(PATH)
CHASE_HEADERS = ["Date of\nTransaction", "Merchant Name or Transaction Description","$ Amount"]


def set_logger() -> None:
    ''' Enable logging to file & console '''
    LOG_PATH = os.getcwd() + "/ingest_data.log"
    # Empty old run
    with open(LOG_PATH, 'w') as lf:
        lf.write('New run.')
    log_fmt = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    file_handler = logging.FileHandler(LOG_PATH)
    rootLogger.setLevel(logging.INFO)
    file_handler.setFormatter(log_fmt)
    rootLogger.addHandler(file_handler)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(log_fmt)
    rootLogger.addHandler(stdout_handler)



def get_transaction_date(txt_line: str) -> str:
    # TODO: add year & return as datetime
    trans_date_mtch = re.match('([0-9]{2}\/[0-9]{2})', txt_line, flags=re.IGNORECASE)
    if not trans_date_mtch:
        return None
    trans_date_grps = trans_date_mtch.groups()
    trans_date = trans_date_grps[0]
    return trans_date


def get_transaction_amount(txt_line: str) -> float:
    amt = None
    amt_mtchs = re.findall('\s+(-*[0-9]*,*[0-9]*.[0-9]{2})\n*', txt_line) 
    for m in amt_mtchs:
        amt = m.replace(',','')
    return float(amt)


def trans_text_to_df(txt: str) -> pd.DataFrame:
    ''' Take transaction text and convert it to a DataFrame '''
    txt_lines = txt.split('\n')
    l = []
    for line in txt_lines:
        if line:
            trans_date = get_transaction_date(line)
            if not trans_date:
                continue
            amt = get_transaction_amount(line)
            desc = line.split(trans_date)[1].split(str(amt))[0].strip()
            l.append({
                'Transaction Date': trans_date,
                'Amount': amt,
                'Description': desc
            })
    return pd.DataFrame(l)


def get_opening_closing_date(page: str) -> tuple[datetime, datetime]:
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
    ''' Grab pdfs from `PDF_DIR` and extract transaction tables'''
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
                purchases_this_period = get_purchases_this_period(text)
            # Get transaction table
            if CHASE_HEADERS[0] in text:
                found_transaction_table = True 
                # Transaction table is from "$ Amount" to 'Total fees charged'
                this_pg_transaction_tbl = text.split(CHASE_HEADERS[-1])[1]
                this_pg_transaction_tbl = this_pg_transaction_tbl.split('Total fees charged')[0]
                # Sometimes the table goes into a new page, in which case "PAYMENTS AND OTHER CREDITS" is on the first
                transaction_table_text += this_pg_transaction_tbl.split('PAYMENTS AND OTHER CREDITS')[0]
        logger.info(f"Isolated transaction table:\n{transaction_table_text}")
        # Convert table text into DataFrame
        transaction_df = trans_text_to_df(transaction_table_text)
        transaction_df['Opening Date'] = open_dt
        transaction_df['Closing Date'] = close_dt
        transaction_df['Purchases this Period'] = purchases_this_period
        logger.info(transaction_df)
        pdf_data.append(transaction_df)
        logger.info(f'## Done with {filename} ##')
        if not found_transaction_table:
            m = f"Couldnt find table in {filename}"
            logger.error(m)
            raise Exception(m)


if __name__ == "__main__":
    set_logger()
    get_pdf_data()
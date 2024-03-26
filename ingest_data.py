from pypdf import PdfReader
import os 
import logging
import sys 
import pandas as pd
import re

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


def trans_text_to_df(txt: str) -> pd.DataFrame:
    ''' Take transaction text and convert it to a DataFrame '''
    txt_lines = txt.split('\n')
    l = []
    for line in txt_lines:
        if line:
            trans_date_mtch = re.match('([0-9]{2}\/[0-9]{2})', line, flags=re.IGNORECASE)
            if not trans_date_mtch:
                continue
            trans_date_grps = trans_date_mtch.groups()
            trans_date = trans_date_grps[0]
            amt_mtch = re.search('\s+(-*[0-9]*,*[0-9]*.[0-9]{2})\n*', line) 
            amt_grps = amt_mtch.groups()
            amt = amt_grps[-1]
            desc = line.split(trans_date)[1].split(amt)[0].strip()
            l.append({
                'trans_date': trans_date,
                'amt': amt,
                'desc': desc
            })
    return pd.DataFrame(l)


def get_pdf_data(pdf_dir:str=PDF_DIR) -> list[pd.DataFrame]:
    ''' Grab pdfs from `PDF_DIR` and extract transaction tables'''
    for filename in os.listdir(pdf_dir):
        logger.info(f'## Processing {filename} ##')
        reader = PdfReader(pdf_dir + '\\' + filename)
        number_of_pages = len(reader.pages)
        found_transaction_table = False
        transaction_table_text = ''
        for pg_num in range(0, number_of_pages):
            page = reader.pages[pg_num]
            text = page.extract_text()
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
        logger.info(f'## Done with {filename} ##')
        if not found_transaction_table:
            m = f"Couldnt find table in {filename}"
            logger.error(m)
            raise Exception(m)


if __name__ == "__main__":
    set_logger()
    get_pdf_data()
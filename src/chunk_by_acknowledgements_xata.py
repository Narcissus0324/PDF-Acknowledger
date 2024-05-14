import concurrent.futures
import os
import pickle
from dotenv import load_dotenv
from tools.unstructure_pdf import unstructure
from xata.client import XataClient

load_dotenv()

xata = XataClient(
    api_key=os.getenv("XATA_API_KEY"), db_url=os.getenv("XATA_DB_URL")
)

table_name = "ESG"
columns = ["id", "language"]

def fetch_all_records(xata, table_name, columns, page_size=1000):
    '''从Xata数据库获取所有记录'''
    all_records = []
    cursor = None
    more = True

    while more:
        page = {"size": page_size}
        if not cursor:
            results = xata.data().query(
                table_name,
                {
                    "page": page,
                    "columns": columns,
                },
            )
        else:
            page["after"] = cursor
            results = xata.data().query(
                table_name,
                {
                    "page": page,
                    "columns": columns,
                },
            )

        all_records.extend(results["records"])
        cursor = results["meta"]["page"]["cursor"]
        more = results["meta"]["page"]["more"]

    return all_records

records = fetch_all_records(xata, table_name, columns)

def extract_acknowledgements(text_list):
    '''提取致谢部分'''
    ack_start = None
    ack_end = None
    for i, text in enumerate(text_list):
        if 'acknowledgements' in text.lower():
            ack_start = i
        if ack_start is not None and 'references' in text.lower():
            ack_end = i
            break
    if ack_start is not None:
        if ack_end is None:
            return text_list[ack_start:]
        else:
            return text_list[ack_start:ack_end]
    return []

def process_pdf(record):
    '''处理PDF文件，提取文本，并保存为pickle和txt文件'''
    record_id = record["id"]
    if record["language"] == "eng":
        language = ["eng"]
    else:
        language = [record["language"], "eng"]

    text_list = unstructure(
        pdf_name="download/" + record_id + ".pdf", languages=language
    )

    acknowledgements = extract_acknowledgements(text_list)

    if acknowledgements:
        with open("esg_pickle/" + record_id + ".pkl", "wb") as f:
            pickle.dump(acknowledgements, f)

        text_str = "\n----------\n".join(acknowledgements)

        with open("esg_txt/" + record_id + ".txt", "w") as f:
            f.write(text_str)

# 使用多进程方式处理所有PDF文件
with concurrent.futures.ProcessPoolExecutor(max_workers=16) as executor:
    executor.map(process_pdf, records)

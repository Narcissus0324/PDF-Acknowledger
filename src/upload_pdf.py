import os
import mimetypes
import json
from dotenv import load_dotenv
from xata.client import XataClient

load_dotenv()

xata = XataClient(api_key=os.getenv("XATA_API_KEY"), db_url=os.getenv("XATA_DB_URL"))

def upload_file(table_name, record_id, file_path, column_name):
    '''上传文件到指定的记录和列'''
    content_type, _ = mimetypes.guess_type(file_path)
    with open(file_path, "rb") as file_content:
        response = xata.files().put(
            table_name=table_name,
            record_id=record_id,
            column_name=column_name,
            data=file_content,
            content_type=content_type,
        )
        return response

upload_dir = "../upload"
for file_name in os.listdir(upload_dir):
    file_path = os.path.join(upload_dir, file_name)
    _, file_extension = os.path.splitext(file_name)  # 获取文件后缀

    if file_extension.lower() == ".pdf":
        file_name_without_ext = os.path.splitext(file_name)[0]
        record_data = {
            "name": file_name_without_ext,
            "contentType": mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        }
        insert_response = xata.records().insert("ESG_Reports", record_data)

        if insert_response.is_success():
            # 解析JSON响应
            response_data = json.loads(insert_response.content.decode('utf-8'))
            record_id = response_data['id']  # 从解析的数据中获取ID
            print(f"Record created: {record_id}")

            # 上传文件
            file_upload_response = upload_file("ESG_Reports", record_id, file_path, "report")
            if file_upload_response.is_success():
                print(f"File uploaded successfully: {file_name}")
            else:
                print(f"Failed to upload file: {file_name}, Response: {file_upload_response}")
        else:
            print(f"Failed to create record for {file_name}: {insert_response}")

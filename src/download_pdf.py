import mimetypes
import os
from dotenv import load_dotenv
from xata.client import XataClient

load_dotenv()

def get_extension_from_content_type(content_type):
    '''根据内容的MIME类型确定文件扩展名'''
    extension = mimetypes.guess_extension(content_type)
    return extension

xata = XataClient(api_key=os.getenv("XATA_API_KEY"), db_url=os.getenv("XATA_DB_URL"))

# 查询数据库获取记录
data = xata.data().query(
    "ESG_Reports",
    {
        "columns": ["id"],
        "page": {"size": 1000},
    },
)

# 遍历查询结果并下载文件
for record in data["records"]:
    file = xata.files().get("ESG_Reports", record["id"], "report")
    # print(file.headers)  # 打印所有头信息，以查看实际包含哪些头
    content_type = file.headers.get('Content-Type', file.headers.get('content-type'))

    if content_type:
        ext = get_extension_from_content_type(content_type)
    else:
        print(f"Content-Type header not found for record ID: {record['id']}")
        ext = '.pdf'  # 假设默认扩展名为.pdf，可以根据你的实际情况调整

    with open("../download/" + record["id"] + ext, "wb") as f:
        f.write(file.content)
    print(f"Downloaded {record['id']}{ext}")

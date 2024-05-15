import os
from xata.client import XataClient
from dotenv import load_dotenv

load_dotenv()

xata = XataClient(api_key=os.getenv("XATA_API_KEY"), db_url=os.getenv("XATA_DB_URL"))

# 定义ESG_Reports表的模式
table_schema = {
    "columns": [
        {
            "name": "name",
            "type": "string",
            "notNull": True,
            "defaultValue": "Unnamed Report"
        },
        {
            "name": "report",
            "type": "file"
        },
        {
            "name": "contentType",
            "type": "string"
        }
    ]
}

# 创建ESG_Reports表并应用其模式
create_table_response = xata.table().create("ESG_Reports")
assert create_table_response.is_success(), "Failed to create table: " + str(create_table_response)
resp = xata.table().set_schema("ESG_Reports", table_schema)
assert resp.is_success(), "Failed to set schema: " + str(resp)

# 定义ESG表的模式
'''
schema_esg = {
    "columns": [
        {"name": "language", "type": "string"},
        {"name": "acknowledgements", "type": "text", "optional": True}
    ]
}
'''

# 创建ESG表并应用其模式
'''
esg_response = xata.table().create("ESG")
assert esg_response.is_success(), "Failed to create ESG table"
resp = xata.table().set_schema("ESG", schema_esg)
assert resp.is_success(), f"Failed to set schema for ESG: {resp}"
'''

print("Database tables created successfully.")

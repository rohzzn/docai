import os

from langchain_box.document_loaders import BoxLoader
from langchain_box.retrievers import BoxRetriever
from langchain_box.utilities import BoxAuth, BoxAuthType


BOX_DEVELOPER_TOKEN = os.environ.get("BOX_DEVELOPER_TOKEN")

# auth = BoxAuth(
#     auth_type=BoxAuthType.CCG,
#     box_client_id=box_client_id,
#     box_client_secret=box_client_secret,
#     box_enterprise_id=box_enterprise_id
# )

retriever = BoxRetriever(
    # box_auth=auth,
    box_developer_token=BOX_DEVELOPER_TOKEN
)
res = retriever.invoke("who maintains the hippa complaints?")
print(res)

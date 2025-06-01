import os
os.environ["OPENAI_API_KEY"] = '###'

from openai import OpenAI

client = OpenAI()

vector_store_file = client.vector_stores.files.create(
  vector_store_id="vs_67fdabd712148191a85838e6b1a872c9",
  file_id="file-8XYoVjrTsdNPBQvncX4Jm2"
)
print(vector_store_file)

# files=client.files.create(
#   file=open("KB.json", "rb"),
#   purpose="assistants"
# )
# print(files)

# vector_store = client.vector_stores.create(
#   name="My Movie Store"
# )
# print(vector_store)

# vector_stores = client.vector_stores.list()
# print(vector_stores)

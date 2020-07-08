# from utils.db import db
# from typing import List
# import pandas as pd
# from fastapi import APIRouter


# router = APIRouter()


# def import_excel(file)




# @router.post("/import")
# async def import_products(
#   overwrite: bool=False, 
#   files: List[UploadFile],
#   file_type: str,
#   text_sep: str = None,
# ):
#   """
#   Collection to import in will be defined by file/sheet name

#   Each excel sheet or text file must contain a header row.
#   Each column must be a valid record field

#   Json import can be from single file with collection as root keys, 
#   or with multiple files each containing an array or records
#   """

#   if file_type == 'text':
#     def df_from_text(f: UploadFile):
#       return pd.read_csv(f.file, sep=text_sep)

#     data = { f.filename: df_from_text(f.file) for f in files }


  



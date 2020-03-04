from typing import List
from fastapi import APIRouter, UploadFile, HTTPException, Form, File
from fastapi.encoders import jsonable_encoder
from utils.db import db
from utils.api import APIResponse
from .models import ProductData, ProductDoc, ProductFull
from utils.file import UserFile
import os
import traceback
router = APIRouter()

product_db = db.collection('Product')



# ALL ROUTES BEGIN WITH 'product'
@router.get("/")
async def get_product_list(
  limit: int = None, # return a limited number of results
  code: str = None, # filter by code
):

  list =  db.aql.execute("""
    LET search = CONCAT('%', @code, '%')
    FOR p IN Product
      FILTER !p.trash && LIKE(p.code, search, true)
      LIMIT @limit
      SORT p.code
      RETURN p
    """, bind_vars={"code": code, "limit": limit})

  results = [ProductData(**p) for p in list]
  return results




# =================================================
#  POST
# =================================================
@router.post("/")
async def create_product(
  code: str = Form(...),
  description: str = Form(''),
  image: UploadFile = File(None)
):
  
  # Map form data
  try:
    new_product = ProductDoc(code=code, description=description)
    prepped_data = jsonable_encoder(new_product, by_alias=True, include_none=False )

  except Exception as e:
    error_str = traceback.format_exc()
    raise HTTPException(
      status_code=400,
      detail=f'The data provided cannot be read properly: \n{error_str}'
    )
  
  # Check if code is present
  if product_db.find({'code': code, 'trash': False}).count():
    status_code = 400
    response = {
      "status": status_code,
      "message": "A product with the same code already exists"
    }
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  # Insert into database
  try:
    db_response = product_db.insert(prepped_data, return_new=True)
  except Exception:
    status_code = 500
    error_str = traceback.format_exc()
    response = {
      "status": status_code,
      "message": "There was a problem saving the data into the database. Please contact support if it happens again",
      "error": error_str
    }
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  # Save image
  if image:

    media_directory = "/Volumes/Luca/DEV/Progress/WebApps/Library/public/pics/products"
    new_product_key = db_response['_key']
    # Define product docs folder (named after product ID within the Product folder)
    product_path = os.path.join(
      media_directory, 
      #db_response['_key']
      )

    # If product folder is not present, create it
    if not os.path.isdir(product_path):
      os.mkdir(product_path)
    
    # Try saving file
    try: 
      filename = f'{new_product_key}.jpeg'

      with open(os.path.join(product_path, filename), 'wb+') as f:
        image_data = await image.read()
        f.write(image_data)
      
    except:
      raise HTTPException(
        status_code=500,
        detail="Could not save image"
      )


  # Close request and return response
  status_code = 200
  message = "Product created"
  response = APIResponse(
    status_code=status_code,
    message=message,
    # Arango replies by sending a json that includes id, key, rev and 
    # then again the whole document nested in the main objecy, 
    # thus duplicating the above keys. Below we get only the whole document.
    detail=db_response['new']
  )

  return response




# =================================================
#  DELETE
# =================================================
@router.delete("/{product_key}")
async def delete_product(product_key):  
  product_to_trash = product_db.get(product_key)

  try: 
    updated_product = product_db.update(
      { '_key': product_key, 'trash': True}, 
      return_new=True
    )['new']
    response = APIResponse(
      status_code=200,
      message=f"Product {updated_product['code']} (KEY: {product_key}) moved to trash",
      detail=updated_product
    )
    return response

  except:
    status_code=500
    response = {
      "status": status_code,
      "message": "Couldn't delete product on the db",
      "error": traceback.format_exc()
    }
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

# =================================================
#  PATCH
# =================================================
@router.patch("/{product_key}")
async def udpate_product(
  product_key: str = None,
  updated_fields: dict = {}
):

  product_to_update = product_db.get(product_key)
  try:
    updated_product = product_db.update(
      { '_key': product_key, **updated_fields }, 
      return_new=True
    )['new']
    # print(updated_product)
    response = APIResponse(
      status=200,
      message=f"Product {updated_product['code']} (KEY: {updated_product['_key']}) updated",
      detail=updated_product
    )
    return response

  except:
    status_code = 500
    response = {
      "status": status_code,
      "message": "Couldn't update product on the db",
      "error": traceback.format_exc()
    }
    raise HTTPException(
      status_code=status_code,
      detail=response
    )  


# =================================================
#  PUT (PRODUCT)
# =================================================
@router.put("/{product_key}")
async def replace_product(
  product_key: str, 
  new_product_data: ProductData,
):

  # new_product_data.key = product_key
  # can comment the above out, since the key is already included in the data
  prepped_data = jsonable_encoder(new_product_data, by_alias=True)
  saved_product = product_db.replace(prepped_data, return_new=True)['new']

  return saved_product


# =================================================
#  POST (DOCS)
# =================================================
@router.post("/{product_key}/doc")
async def update_docs(
  product_key: str,
  new_doc: UploadFile =  File(...)
):

  print(new_doc)
  doc = UserFile.product_doc(
    append_path=product_key,
    file=new_doc,
    name=new_doc.filename
  )
  try:
    await doc.write_file()
  except:
    error_str = traceback.format_exc()
    status_code = 400
    response = {
      'status': status_code,
      'message': 'There was an error writing the file to disk',
      'error_str': error_str
    }
    raise HTTPException(
      status_code = status_code,
      detail = response
    )

  return doc.name

# =================================================
#  DELETE (DOCS)
# =================================================
@router.delete("/{product_key}/doc/{doc_name}")
async def delete_doc(
  product_key: str,
  doc_name: str
):
  print(doc_name)
  doc = UserFile.product_doc(
    append_path=product_key, 
    name=doc_name
  )

  doc.delete_file()


# =================================================
#  PUT (IMAGE)
# =================================================
# @router.put("/{product_key}")



# =================================================
#  GET
# =================================================
@router.get("/{product_key}", response_model=ProductFull)
async def get_product_data(product_key: str):
  product = ProductFull(**product_db.get(product_key))


  # All the following can be removed if doc names are included in the DB
  media_directory = "/Volumes/Luca/DEV/Progress/WebApps/Library/public/docs"
  docs_path = os.path.join(media_directory, product_key)

  def check_pdf(filename):
    return filename.name.split('.')[-1] == 'pdf'

  if os.path.isdir(docs_path):
    doc_list = [ doc for doc in os.scandir(docs_path) if check_pdf(doc) ]
  else:
    doc_list = []

  def doc_data(doc):
    return ProductDoc(
      name=doc.name, 
      size=doc.stat().st_size
    )

  product.docs = list(map(doc_data, doc_list))

  return product
  






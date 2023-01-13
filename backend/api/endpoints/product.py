import os
import traceback
from typing import List
from fnmatch import fnmatch

from fastapi import APIRouter, Form, File, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder

from models.product import *
from utils.api import APIResponse
from utils.db import db
from utils.file import UserFile
from utils.product import *

router = APIRouter()

product_db = db.collection('Product')



# ALL ROUTES BEGIN WITH 'product'

# =================================================
#  GET / : GET PRODUCT LIST
# =================================================
@router.get("")
async def get_product_list(
  offset: int = None,
  limit: int = None, # return a limited number of results
  search: str = None, # filter by code
  details: bool = False
):

  product_list =  db.aql.execute(
    Queries.GET_PRODUCT_LIST,
    bind_vars=dict(
      search = search,
      limit = limit,
      details = details,
      offset = offset
    )
  )

  def validate(data):
    return ProductDetails(**data) if details else ProductBaseData(**data)

  results = [validate(p) for p in product_list]

  return results




# =================================================
#  POST / : CREATE PRODUCT
# =================================================
@router.post("", status_code=201)
async def create_product(
  code: str = Form(...),
  description: str = Form(''),
  image: UploadFile = File(None)
):

  # Map form data
  try:
    new_product = ProductDetails(code=code, description=description)

  except Exception as e:
    error_str = traceback.format_exc()
    raise HTTPException(
      status_code=400,
      detail=f'The data provided cannot be read properly: \n{error_str}'
    )

  # Check if code is present
  if product_db.find(dict(code=code, trash=False)).count():
    status_code = 400
    response=dict(
      status=status_code,
      message="A product with the same code already exists"
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  # Save data
  try:
    # Save image
    if image:
      new_product.image = True

      product_image = UserFile.product_media(
        append_path=db_response['_key'],
        file=image,
      )

      try:
        await product_image.write_file('image.jpg')

      except:
        raise HTTPException(
          status_code=500,
          detail="Could not save image"
        )

    tx = db.begin_transaction(write=["Product"])
    prepped_data = jsonable_encoder(new_product, by_alias=True, exclude_none=True )
    db_response = tx.collection("Product").insert(prepped_data, return_new=True)
    tx.commit_transaction()


  except Exception:
    status_code = 500
    error_str = traceback.format_exc()
    response=dict(
      status=status_code,
      message="There was a problem saving the data into the database. Please contact support if it happens again",
      error=error_str
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
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
#  DELETE /PRODUCT_KEY : DELETE PRODUCT
# =================================================
@router.delete("/{product_key}")
async def delete_product(product_key):
  product_to_trash = product_db.get(product_key)

  try:
    updated_product = product_db.update(dict(_key=product_key, trash=True), return_new=True)['new']
    response = APIResponse(
      status_code=200,
      message=f"Product {updated_product['code']} (KEY: {product_key}) moved to trash",
      detail=updated_product
    )
    return response

  except:
    status_code=500
    response=dict(
      status=status_code,
      message="Couldn't delete product on the db",
      error=traceback.format_exc()
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

# =================================================
#  PATCH /PRODUCT_KEY : UPDATE PRODUCT (SPECIFC PROPERTIES)
# =================================================
@router.patch("/{product_key}")
async def udpate_product(
  product_key: str = None,
  updated_fields: dict = dict()
):

  product_to_update = product_db.get(product_key)
  try:
    updated_product = product_db.update(
      dict(_key=product_key, **updated_fields),
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
    response=dict(
      status=status_code,
      message="Couldn't update product on the db",
      error=traceback.format_exc()
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )


# =================================================
#  PUT /PRODUCT_KEY : REPLACE PRODUCT
# =================================================
@router.put("/{product_key}")
async def replace_product(
  product_key: str,
  new_product_data: ProductDetails,
):

  # new_product_data.key = product_key
  # can comment the above out, since the key is already included in the data
  prepped_data = jsonable_encoder(new_product_data, by_alias=True)
  saved_product = product_db.replace(prepped_data, return_new=True)['new']

  return saved_product


# =================================================
#  POST /PRODUCT_KEY/DOCS : SAVE DOC
# =================================================
@router.post("/{product_key}/doc")
async def save_doc(
  product_key: str,
  new_doc: UploadFile =  File(...)
):

  doc = UserFile.product_media(
    append_path=f"{product_key}/doc",
    file=new_doc,
    name=new_doc.filename
  )
  try:
    await doc.write_file()
  except:
    error_str = traceback.format_exc()
    status_code = 400
    response=dict(
      status=status_code,
      message="There was an error writing the file to disk",
      error_str=error_str
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
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

  doc = UserFile.product_media(
    append_path=f'{product_key}/doc',
    name=doc_name
  )

  doc.delete_file()


# =================================================
#  PUT (IMAGE)
# =================================================
@router.put("/{product_key}/image")
async def replace_product_image(
  product_key: str,
  new_image: UploadFile = File(...)
):
  # extension = new_image.filename.split('.')[-1]
  img = UserFile.product_media(append_path=product_key, file=new_image)
  filename = 'image.jpg'
  product_db.update(dict(
    _key=product_key,
    image=True
  ))
  await img.write_file(filename)
  return APIResponse(message="File saved correctly")



# =================================================
#  DELETE (IMAGE)
# =================================================
@router.delete("/{product_key}/image")
async def replace_product_image(product_key: str):
  # extension = new_image.filename.split('.')[-1]
  img = UserFile.product_media(append_path=product_key)
  img.delete_file('image.jpg')
  product_db.update(dict(
    _key=product_key,
    image=False
  ))

# =================================================
#  GET /PRODUCT_KEY : GET PRODUCT DATA
# =================================================
@router.get("/{product_key}", response_model=ProductFull)
async def get_product_data(product_key: str):
  try:
    product = ProductFull(**product_db.get(product_key))
    product.docs = get_product_docs(product_key)
    return product

  except:
    error_str = traceback.format_exc()
    status_code = 500
    response=dict(
      status=status_code,
      message="There was an error getting data from the database.",
      error_str=error_str
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )








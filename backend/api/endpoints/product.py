import os
import traceback

from fastapi import APIRouter, Form, File, HTTPException, UploadFile, Body
from fastapi.encoders import jsonable_encoder

from utils.kpi import Queries as ProductStatQueries
from models.product import *
from models.process import PhaseData
from utils.api import APIResponse
from utils.db import db
from utils.dt import timestamp
from utils.file import FileHandler
from utils.product import *
from utils.process import Queries as ProcessQueries

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
    new_product = ProductDetails(
      code=code,
      description=description,
      created=timestamp()
    )

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


  if image:
    new_product.image = True

  # Save data
  try:
    tx = db.begin_transaction(write=["Product"])
    prepped_data = jsonable_encoder(new_product, by_alias=True, exclude_none=True )
    db_response = tx.collection("Product").insert(prepped_data, return_new=True)

    # Save image
    if image:
      product_image = FileHandler.product_media(
        object_key=db_response['_key'],
        file=image,
      )

      try:
        await product_image.write_file(custom_name='image.jpg')

      except:
        tx.abort_transaction()
        raise HTTPException(
          status_code=500,
          detail="There was an error saving the image"
        )

    tx.commit_transaction()

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

  except Exception:
    tx.abort_transaction()
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


# =================================================
#  POST /PRODUCT_KEY/COPY : COPY PRODUCT
# =================================================
@router.post("/copy", status_code=201)
async def copy_product(
  original_product: str = Body(), # Can be product key or code (key default)
  new_code: str = Body(),
  new_description: str = Body(None),
  by_code: bool = Body(default=False)
  ):

  # 0.1 Check no product exists with same code
  if db.collection('Product').find(dict(code=new_code, trash=False)).count():
    raise HTTPException(
      status_code=409,
      detail="A product with the same code already exists"
    )

  # 0.2 Setup transaction
  tx = db.begin_transaction(write=['Product', 'Phase', 'Step', 'requires', 'can_use_print_template'], read=['Operation'])
  product_db = tx.collection('Product')

  # 0.3 Fetch product data
  try:
    if by_code:
      match = dict(code=original_product, trash=False)

    else: # Copy product by key
      match = dict(_key=original_product, trash=False)

    new_product = ProductDetails(**product_db.find(match).next())
    new_product.created = timestamp()

    original_product_code = new_product.code
    original_product_description = new_product.description
    original_product_key = new_product.key

  except StopIteration:
    tx.abort_transaction()
    raise HTTPException(
      status_code=404,
      detail="No product with the provided code or key could be found"
    )

  except Exception:
    tx.abort_transaction()
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

  def copy_print_templates(collection_name, from_key, to_key):
    print_template_cursor = tx.collection('can_use_print_template').find(dict(_from=f'{collection_name}/{from_key}'))
    if print_template_cursor.count() > 0:
      new_print_templates = []
      for edge in print_template_cursor:
        new_print_templates.append(dict(_from=f'{collection_name}/{to_key}', _to=edge['_to']))

      tx.collection('can_use_print_template').insert_many(new_print_templates, silent=True)

  try:
    # 1. CREATE NEW PRODUCT WITH PROVIDED CODE
    new_product.code = new_code
    new_product.description = new_description or original_product_description
    new_product.active = True
    new_product.key = None

    prepped_data = jsonable_encoder(new_product, by_alias=True, exclude_none=True)
    new_product_key = product_db.insert(prepped_data)['_key']

    # 2 COPY PROCESS
    # See also update_process endpoint in endpoints/process.py

    # 2.1 PROCESS: Get process data
    bind_vars = dict(product_key=original_product_key)
    db_process = tx.aql.execute(ProcessQueries.GET_PRODUCTION_PROCESS, bind_vars=bind_vars)
    process_data = [PhaseData(**phase) for phase in db_process]

    # 2.2 PROCESS: Initialize new phase sequence
    new_process_phases = []

    # COPY PHASES, STEPS & BOM
    for phase in process_data:

      # 3.1 PHASE: Update original phase data
      phase.product_key = new_product_key

      # 4.1 STEP: Initialize new step_sequence
      new_step_sequence = []

      # 4.2 STEP: Copy steps
      for step in phase.steps:
        # Exclude key field if not present so DB creates new record
        prepped_step_data = jsonable_encoder(step, by_alias=True, exclude={'key'})
        new_step_key = tx.insert_document('Step', prepped_step_data)['_key']

        new_step_sequence.append(new_step_key)

        # 4.3 STEP: Copy step media files
        step_media = FileHandler.step_media(step.key)
        if os.path.isdir(step_media.folder_path):
          step_media.copy_media(new_step_key)

        # 4.4. STEP: Copy print templates
        copy_print_templates('Step', step.key, new_step_key)

      # 3.2 PHASE: create new phase with existing operation key and parameters and new step sequence
      phase.step_sequence = new_step_sequence
      exclude_set = {'id', 'rev', 'steps', 'key'}
      prepped_phase_data = jsonable_encoder(phase, by_alias=True, exclude=exclude_set)
      new_phase_key = tx.insert_document('Phase', prepped_phase_data)['_key']

      # 3.3 PHASE: Insert new ProductPhase relationship
      product_phase_edge = dict(
        _from=f'Product/{new_product_key}',
        _to=f'Phase/{new_phase_key}',
        type='ProductPhase'
      )
      tx.insert_document('requires', product_phase_edge)

      # 3.4 PHASE: Insert new PhaseOperation relationship
      phase_operation_edge = dict(
        _from=f'Phase/{new_phase_key}',
        _to=f'Operation/{phase.operation_key}',
        type='PhaseOperation'
      )
      tx.insert_document('requires', phase_operation_edge)

      # 3.5 PHASE: Copy print templates
      copy_print_templates('Phase', phase.key, new_phase_key)

      # 4.1 BOM: Get BoM for phase
      match = dict(
        _from=f'Phase/{phase.key}',
        type='BomLine'
      )
      phase_bom_cursor = tx.collection('requires').find(match)

      # 4.2 BOM: Update with new phase key and insert
      if phase_bom_cursor.count():
        new_phase_bom = []

        for line in phase_bom_cursor:
          line['_from'] = f'Phase/{new_phase_key}'
          # Remove id fields to make db create new record
          for prop in ['_id', '_key', '_rev']:
            del line[prop]
          new_phase_bom.append(line)

        tx.collection('requires').insert_many(new_phase_bom, silent=True)

      # 2.3 PROCESS: save phase key in new product process
      new_process_phases.append(new_phase_key)

    # 2.4 Update product with new phases
    product_db.update(dict(
      _key=new_product_key,
      process_phases=new_process_phases
    ))

    # 7. Copy product media folder (if present) with new product key
    product_media = FileHandler.product_media(original_product_key)
    if os.path.isdir(product_media.folder_path):
      product_media.copy_media(new_product_key)

    #TODO
    """
    Delete media folders created if something goes wrong
    """

    # 8. Copy product print templates
    copy_print_templates('Product', original_product_key, new_product_key)

    # 9. Commit transaction
    tx.commit_transaction()

    return APIResponse(
      status_code=201,
      message=f"Created product {new_code} as copy of product {original_product_code}.",
      detail=dict(new_product_key=new_product_key)
    )

  except:
    tx.abort_transaction()
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




# =================================================
#  DELETE /PRODUCT_KEY : DELETE PRODUCT
# =================================================
@router.delete("/{product_key}")
async def delete_product(product_key):
  product_to_trash = product_db.get(product_key)

  # TODO: Verify if there's any workorder or active item related
  # How to deal with historical data?

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
      dict(
        _key=product_key,
        updated=timestamp(),
        **updated_fields
      ), return_new=True
    )['new']
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

  doc = FileHandler.product_media(
    object_key=product_key,
    subfolder="doc",
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

  doc = FileHandler.product_media(
    object_key=product_key,
    subfolder='doc',
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
  img = FileHandler.product_media(object_key=product_key, file=new_image)
  filename = 'image.jpg'
  product_db.update(dict(
    _key=product_key,
    updated=timestamp(),
    image=True
  ))
  await img.write_file(custom_name=filename)
  return APIResponse(message="File saved correctly")



# =================================================
#  DELETE (IMAGE)
# =================================================
@router.delete("/{product_key}/image")
async def replace_product_image(product_key: str):
  # extension = new_image.filename.split('.')[-1]
  img = FileHandler.product_media(object_key=product_key)
  img.delete_file('image.jpg')
  product_db.update(dict(
    _key=product_key,
    updated=timestamp(),
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



# =================================================
#  PRODUCT STATS
# =================================================
@router.get('/{product_key}/stats')
async def get_product_stats(product_key: str):
  try:
    stats = db.aql.execute(ProductStatQueries.GET_PRODUCT_STATS, bind_vars=dict(product_key=product_key)).next()
    return stats

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



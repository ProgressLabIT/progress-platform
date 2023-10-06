import traceback

from fastapi import APIRouter, HTTPException

from models.print import PrintTemplateRecord, TemplateAssignmentUpdateList
from utils.api import APIResponse
from utils.db import db
from utils.print import preprocess_template, build_template_assignment_record

router = APIRouter()



# Fetch Print Templates
@router.get('/print-template')
async def find_print_templates(
  product_key: str = None,
  phase_key: str = None,
  issue_key: str = None
  ):
  """Fetch a specific template with full specs or a list of template without basePdf"""
  bind_vars = dict(
    product_key = product_key,
    phase_key = phase_key,
    issue_key = issue_key
  )

  if product_key is None and phase_key is None and issue_key is None:
    cursor = db.collection('PrintTemplate').all()

  else:
    cursor = db.aql.execute("""
      for e in can_use_print_template
      FILTER
          (@phase_key ? e._from == CONCAT('Phase/', @phase_key) : true)
          && (@product_key ? e._from == CONCAT('Product/', @product_key) : true)
          && (@issue_key ? e._from == CONCAT('Issue/', @issue_key) : true)
      return keep(DOCUMENT(PrintTemplate, e._to), '_key', 'name', 'description')
    """, bind_vars=bind_vars)

  result = [t for t in cursor]

  return result


@router.get('/print-template/{template_key}')
async def get_print_template_details(template_key: str):
  template = db.collection('PrintTemplate').get(template_key)
  return preprocess_template(template)


# Create PrintTemplate
@router.post('/print-template')
async def create_print_template(template_data: PrintTemplateRecord):
  try:
    resp = db.collection('PrintTemplate').insert(template_data)
    return APIResponse(
      status_code = 200,
      message = "Print template created successfully",
      detail = dict(template_key=resp['_key'])
    )
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

# Update Print Template
@router.put('/print-template')
async def update_print_template(template_data: PrintTemplateRecord):
  try:
    update = template_data.dict(by_alias=True)
    print(update)
    resp = db.collection('PrintTemplate').update(update)
    return APIResponse(
      status_code = 200,
      message = f"Print template {template_data.key} updated successfully"
    )
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


# Delete Print Template
@router.delete('/print-template/{template_key}')
async def delete_print_template(template_key: str):
  ...



@router.post('/update-template-assignments')
async def update_template_assignments(update=TemplateAssignmentUpdateList):

  context_map = {
    TemplateAssignmentContext.PRODUCT.value: 'Product',
    TemplateAssignmentContext.PHASE.value: 'Phase',
    TemplateAssignmentContext.STEP.value: 'Step',
    TemplateAssignmentContext.ISSUE_TYPE.value: 'IssueType',
  }


  try:
    tx = db.begin_transaction()
    tx.insert_many([build_template_assignment_record(r) for r in update.add])

    delete_list = [build_template_assignment_record(r) for r in update.remove]
    delete_query = """
      FOR d IN @delete_list
        FOR record IN can_use
        FILTER
          record.type == 'TemplateAssignment'
          && record._from = d._from
          && record._to == d._to
        REMOVE record IN can_use
    """
    bind_vars = dict(delete_list=delete_list)
    tx.aql.execute(delete_query, bind_vars=bind_vars)

    tx.commit_transaction()

    return APIResponse(message='Assignments updated correctly')

  finally:
    if tx.transaction_status != 'committed':
      tx.abort_transaction()





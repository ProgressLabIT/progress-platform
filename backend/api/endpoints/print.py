import traceback

from fastapi import APIRouter, HTTPException, Depends
from utils import auth

from models.print import PrintTemplateRecord, TemplateAssignmentUpdate, TemplateAssignmentUpdateType, TemplateAssignmentContext
from utils.api import APIResponse
from utils.db import db
from utils.print import preprocess_template, build_template_assignment_record

router = APIRouter()


# Fetch Print Templates
@router.get('/print-template', dependencies=[Depends(auth.verify_token)])
async def find_print_templates(
  context: TemplateAssignmentContext | None = None,
  context_key: str | None = None,
):
  """Fetch a specific template with full specs or a list of template without basePdf"""
  if context is None:
    cursor = db.aql.execute(
      """
      FOR template IN PrintTemplate

      LET entities = (
        FOR edge IN can_use_print_template
          FILTER edge._to == template._id
          return edge
      )

      SORT template.name
      RETURN MERGE(KEEP(template, '_key', 'name', 'description'), { entities : COUNT(entities) })
      """
    )
  elif context == 'template':
    cursor = db.aql.execute(
      """
      FOR template IN PrintTemplate
      FILTER template._key == @context_key

      LET entities = (
        FOR edge IN can_use_print_template
          FILTER edge._to == template._id
          return edge
      )

      SORT template.name
      RETURN MERGE(KEEP(template, '_key', 'name', 'description'), { entities : COUNT(entities) })
      """,
      bind_vars=dict(
        context_key=context_key,
      )
    )
  else:
    context_to_collection = dict(
      product='Product',
      phase='Phase',
      step='Step',
      issue_type='IssueType'
    )

    cursor = db.aql.execute(
      """
      FOR edge IN can_use_print_template
        FILTER edge._from == @from_id
        LET template = DOCUMENT(PrintTemplate, edge._to)
        SORT template.name
        RETURN KEEP(template, '_key', 'name', 'description')
      """,
      bind_vars=dict(
        from_id=f'{context_to_collection.get(context)}/{context_key}',
      )
    )

  result = [PrintTemplateRecord(**t) for t in cursor]

  return result


@router.get('/print-template/{template_key}',
    dependencies=[Depends(auth.verify_token)])
async def get_print_template_details(template_key: str):
  template = db.collection('PrintTemplate').get(template_key)
  return preprocess_template(template)


# Create PrintTemplate
@router.post('/print-template',
    dependencies=[Depends(auth.verify_token)])
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
@router.put('/print-template',
    dependencies=[Depends(auth.verify_token)])
async def update_print_template(template_data: PrintTemplateRecord):
  try:
    update = template_data.dict(by_alias=True)
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
@router.delete('/print-template/{template_key}',
    dependencies=[Depends(auth.verify_token)])
async def delete_print_template(template_key: str):
  """Delete template and linked"""
  try:
    tx = db.begin_transaction(write=['PrintTemplate', 'can_use_print_template'])

    tx.collection('PrintTemplate').delete(template_key)
    tx.collection('can_use_print_template').delete_match(filters=dict(_to=f'PrintTemplate/{template_key}'))

    tx.commit_transaction()

    return APIResponse(message = "Template deleted successfully")
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())



@router.post('/update-template-assignments',
    dependencies=[Depends(auth.verify_token)])
async def update_template_assignments(updates: list[TemplateAssignmentUpdate]):

  try:
    tx = db.begin_transaction(write=['can_use_print_template'])

    to_add = [build_template_assignment_record(u) for u in updates if u.type == TemplateAssignmentUpdateType.ADD]
    if to_add:
      tx.collection('can_use_print_template').insert_many(to_add)

    to_remove = [build_template_assignment_record(u) for u in updates if u.type == TemplateAssignmentUpdateType.REMOVE]
    if len(to_remove):
      tx.aql.execute(
        """
        FOR d IN @to_remove
          FOR record IN can_use_print_template
          FILTER
            record._from == d._from
            && record._to == d._to
          REMOVE record IN can_use_print_template
        """,
        bind_vars=dict(to_remove=to_remove)
      )

    tx.commit_transaction()

    return APIResponse(message='Assignments updated correctly')

  finally:
    if tx.transaction_status() != 'committed':
      tx.abort_transaction()





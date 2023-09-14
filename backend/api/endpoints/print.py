import traceback

from fastapi import APIRouter

from models.print import PrintTemplateRecord
from utils.api import APIResponse
from utils.db import db

router = APIRouter()



# Fetch Print Templates
@router.get('/print-template')
async def get_print_templates(key: str = None):
  """Fetch a specific template with full specs or a list of template without basePdf"""
  bind_vars = dict(key = key)
  cursor = db.aql.execute("""
    FOR t IN PrintTemplate
    FILTER @key ? t._key == @key : true
    LET slim_template = UNSET(t.template, 'basePdf')
    RETURN @key ? t : MERGE(t, {specs: slim_template})
  """, bind_vars=bind_vars)

  result = PrintTemplateRecord(**cursor.next()) if key else [PrintTemplateRecord(**t) for t in cursor]

  return result


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
  ...


# Delete Print Template
@router.delete('/print-template/{template_key}')
async def delete_print_template(template_key: str):
  ...

from models.print import PrintTemplateRecord, TemplateAssignmentUpdate

def preprocess_template(template):
  model = PrintTemplateRecord(**template)
  return model.dict(exclude_none=True, by_alias=True)


def build_template_assignment_record(update: TemplateAssignmentUpdate):
  return dict(
    _from = context_map[update.context] + '/' + update.context_key,
    _to = 'PrintTemplate/' + update.template_key
  )


import base64
import io
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple

from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from weasyprint import HTML

from utils.config import get_config
from utils.db import db
from utils.serial import Queries

def get_company_info() -> Dict[str, str]:
  """Get company name and logo path from config"""
  try:
    company_name = "Progress Platform"  # Default fallback
    company_logo_path = None

    # Get company name from config
    try:
      company_name_config = db.collection('Config').get('company_name')
      if company_name_config and company_name_config.get('value'):
        company_name = company_name_config['value']
    except Exception:
      pass

    # Get company logo path from config
    try:
      company_logo_config = db.collection('Config').get('company_logo')
      if company_logo_config and company_logo_config.get('value'):
        logo_path = company_logo_config['value']
        if os.path.exists(logo_path):
          company_logo_path = logo_path
    except Exception:
      pass

    return {
      'name': company_name,
      'logo_path': company_logo_path
    }
  except Exception:
    return {
      'name': "Progress Platform",
      'logo_path': None
    }


def get_company_logo_base64(logo_path: str) -> str:
  """Convert company logo to base64 data URI for embedding in HTML"""
  try:
    if not logo_path or not os.path.exists(logo_path):
      return ""

    with open(logo_path, 'rb') as f:
      logo_data = f.read()

    # Determine MIME type based on file extension
    ext = os.path.splitext(logo_path)[1].lower()
    mime_type = 'image/png'  # Default
    if ext == '.jpg' or ext == '.jpeg':
      mime_type = 'image/jpeg'
    elif ext == '.svg':
      mime_type = 'image/svg+xml'
    elif ext == '.gif':
      mime_type = 'image/gif'
    elif ext == '.webp':
      mime_type = 'image/webp'

    logo_base64 = base64.b64encode(logo_data).decode('ascii')
    return f"data:{mime_type};base64,{logo_base64}"
  except Exception:
    return ""

def fetch_dhr_data(serial_key: str, include_step_data: bool = False) -> dict[str, Any]:
  """Fetch serial and product data for DHR generation"""
  aql = """
    LET s = DOCUMENT(Serial, @serial_key)
    FILTER s != null
    LET product = s.product_key ? DOCUMENT(Product, s.product_key) : null
    LET wo = s.wo_key ? DOCUMENT(WorkOrder, s.wo_key) : null

    LET fields = (
      FOR d IN NOT_NULL(s.data, [])
        LET cf = d.custom_field_key ? DOCUMENT(CustomField, d.custom_field_key) : null
        LET label = d.label ? d.label : (cf ? (cf.default_label ? cf.default_label : cf.name) : '')
        LET phase = d.phase_key ? DOCUMENT(Phase, d.phase_key) : null
        LET last_event = d.last_updated ? DOCUMENT(Event, d.last_updated) : null
        LET last_user = last_event && last_event.user_key ? DOCUMENT(User, last_event.user_key) : null
        RETURN {
          label,
          form_field_key: d.form_field_key,
          value: d.value,
          phase_key: d.phase_key,
          phase_alias: phase ? (phase.alias || phase.code || phase._key) : null,
          field_type: cf ? cf.type : null,
          last_updated_ts: last_event ? last_event.timestamp : null,
          last_updated_user: last_user ? { name: last_user.name, surname: last_user.surname } : null
        }
    )

    // Get step execution data for this specific serial
    LET step_data = (wo && @include_step_data) ? (
      LET batches = (FOR b IN 1..1 INBOUND s batch_serial SORT b.end RETURN b)
      LET jobs = UNIQUE(batches[*].job_key)[* RETURN DOCUMENT(Job, CURRENT)]
      FOR j IN jobs // should already be sorted by time since batches are sorted
      FOR b IN batches
      FOR step IN NOT_NULL(j.step_sequence, [])
      FOR x IN StepExecutionData
      FILTER x.step_key == step._key && x.batch_key == b._key
      LET operator = x.user_key ? DOCUMENT(User, x.user_key) : null
      RETURN {
        step_key: step._key,
        step_title: step.title,
        batch_key: b._key,
        job_key: j._key,
        timestamp: x.completed,
        phase_key: j.phase_key,
        phase_alias: j.phase_alias,
        operator_username: operator ? operator.username : null,
        operator_name: operator ? CONCAT_SEPARATOR(' ', operator.name, operator.surname) : null
      }
    ) : []

    RETURN {
      serial: { code: s.code, created: s.created, released: s.released },
      product_code: product ? product.code : null,
      product_description: product ? product.description : null,
      wo_phase_sequence: wo ? wo.phase_sequence : [],
      wo_code: wo ? wo.wo_code : null,
      project_code: wo ? wo.project_code : null,
      fields,
      step_data
    }
  """

  return db.aql.execute(aql, bind_vars=dict(serial_key=serial_key, include_step_data=include_step_data)).next()


def safe_text(value) -> str:
  """Convert various data types to safe text for display"""
  if value is None:
    return ''
  if isinstance(value, (int, float)):
    return str(value)
  if isinstance(value, str):
    return value
  # choices or other dicts
  if isinstance(value, dict):
    return value.get('value') or value.get('name') or json.dumps(value)
  # files or generic lists
  if isinstance(value, list):
    try:
      # if files: list of {name, size}
      names = [v.get('name') if isinstance(v, dict) else str(v) for v in value]
      return ', '.join([n for n in names if n])
    except Exception:
      return json.dumps(value)
  return str(value)


def format_minute(iso_ts) -> str:
  """Format timestamp to 'YYYY-MM-DD HH:MM' format"""
  if iso_ts is None:
    return ''
  try:
    if isinstance(iso_ts, str):
      # Basic truncation and T replacement, safe fallback
      return iso_ts.replace('T', ' ')[:16]
    # if datetime
    from datetime import datetime as _dt
    if isinstance(iso_ts, _dt):
      return iso_ts.strftime('%Y-%m-%d %H:%M')
    # numeric epoch milliseconds or seconds
    if isinstance(iso_ts, (int, float)):
      import math
      seconds = iso_ts / 1000 if iso_ts > 1e12 else iso_ts
      from datetime import datetime as _dt2
      return _dt2.utcfromtimestamp(seconds).strftime('%Y-%m-%d %H:%M')
  except Exception:
    pass
  return str(iso_ts)


def format_date_readable(iso_ts) -> str:
  """Format ISO datetime string to human-readable date format like 'January 15, 2024 at 2:30 PM'"""
  if not iso_ts:
    return 'Not specified'
  try:
    from datetime import datetime as _dt
    # Parse ISO format string and format as "January 15, 2024 at 2:30 PM"
    dt = _dt.fromisoformat(iso_ts.replace('Z', '+00:00'))
    return dt.strftime('%B %d, %Y at %I:%M %p')
  except Exception:
    # Fallback to the original format_minute function
    return format_minute(iso_ts)


def get_checkbox_svgs() -> Dict[str, str]:
  """Get SVG definitions for checkbox states"""
  return {
    'checked': (
      '<svg width="12" height="12" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle">'
      '<rect x="1" y="1" width="14" height="14" fill="#fff" stroke="#333" stroke-width="1.5"/>'
      '<path d="M4 8l3 3 5-6" stroke="#111" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
      '</svg>'
    ),
    'unchecked': (
      '<svg width="12" height="12" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle">'
      '<rect x="1" y="1" width="14" height="14" fill="#fff" stroke="#333" stroke-width="1.5"/>'
      '</svg>'
    ),
    'indeterminate': (
      '<svg width="12" height="12" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle">'
      '<rect x="1" y="1" width="14" height="14" fill="#fff" stroke="#333" stroke-width="1.5"/>'
      '<path d="M4 8h8" stroke="#111" stroke-width="2"/>'
      '</svg>'
    )
  }


def process_fields_for_display(fields: List[Dict], wo_phase_sequence: List[str]) -> Tuple[str, bool]:
  """Process fields and group them by phase for display"""
  checkbox_svgs = get_checkbox_svgs()

  # Group fields by phase and build rows with phase alias headers
  fields_by_phase = {}
  phase_alias_map = {}

  for field in fields:
    label = field.get('label') or ''
    field_type = (field.get('field_type') or '').lower()
    value = field.get('value')

    if field_type in ('boolean', 'ternary'):
      if value is True:
        value_html = checkbox_svgs['checked']
      elif value is False:
        value_html = checkbox_svgs['unchecked']
      else:
        value_html = checkbox_svgs['indeterminate']
    else:
      value_html = safe_text(value)

    last_minute = format_minute(field.get('last_updated_ts'))
    lu = field.get('last_updated_user') or {}
    if isinstance(lu, dict):
      last_user_name = f"{(lu.get('name') or '').strip()} {(lu.get('surname') or '').strip()}".strip()
    else:
      last_user_name = ''

    phase_key = field.get('phase_key')
    if phase_key not in fields_by_phase:
      fields_by_phase[phase_key] = []
    if phase_key and phase_key not in phase_alias_map:
      phase_alias_map[phase_key] = field.get('phase_alias') or phase_key

    fields_by_phase[phase_key].append({
      'label': label,
      'value_html': value_html,
      'last_updated': last_minute,
      'last_user': last_user_name
    })

  # Order phases by work order phase sequence when available
  ordered_phase_keys = []
  for k in wo_phase_sequence:
    if k in fields_by_phase and k not in ordered_phase_keys:
      ordered_phase_keys.append(k)
  for k in [k for k in fields_by_phase.keys() if k]:
    if k not in ordered_phase_keys:
      ordered_phase_keys.append(k)

  # Build grouped rows HTML and check if we have any data
  rows_html = ''
  has_serial_data = len(fields) > 0

  if None in fields_by_phase:
    rows_html += f"""
      <tr>
        <th class="phase-header" colspan="4">General</th>
      </tr>
    """
    for item in fields_by_phase[None]:
      rows_html += f"""
        <tr>
          <td class="cell">{item['label']}</td>
          <td class="cell">{item['value_html']}</td>
          <td class="cell">{item['last_updated']}</td>
          <td class="cell">{item['last_user']}</td>
        </tr>
      """

  for pk in ordered_phase_keys:
    phase_title = phase_alias_map.get(pk, pk)
    rows_html += f"""
      <tr>
        <th class="phase-header" colspan="4">{phase_title}</th>
      </tr>
    """
    for item in fields_by_phase.get(pk, []):
      rows_html += f"""
        <tr>
          <td class="cell">{item['label']}</td>
          <td class="cell">{item['value_html']}</td>
          <td class="cell">{item['last_updated']}</td>
          <td class="cell">{item['last_user']}</td>
        </tr>
      """

  return rows_html, has_serial_data


def generate_step_data_table(step_data: List[Dict], wo_phase_sequence: List[str]) -> str:
  """Generate HTML for step data table"""
  if not step_data:
    return ''

  # Group step data by phase
  steps_by_phase = {}
  for step in step_data:
    phase_key = step.get('phase_key')
    if phase_key not in steps_by_phase:
      steps_by_phase[phase_key] = []
    steps_by_phase[phase_key].append(step)

  # Order phases by work order phase sequence when available
  ordered_phase_keys = []
  for k in wo_phase_sequence:
    if k in steps_by_phase and k not in ordered_phase_keys:
      ordered_phase_keys.append(k)
  for k in [k for k in steps_by_phase.keys() if k]:
    if k not in ordered_phase_keys:
      ordered_phase_keys.append(k)

  # Build step data table HTML
  step_data_html = """
    <h2>Step Execution Data</h2>
    <table class="table">
      <thead>
        <tr>
          <th>Phase</th>
          <th>Step</th>
          <th>Operator</th>
          <th>Timestamp</th>
        </tr>
      </thead>
      <tbody>"""

  for phase_key in ordered_phase_keys:
    phase_steps = steps_by_phase.get(phase_key, [])
    # Sort steps by timestamp
    phase_steps.sort(key=lambda x: x.get('timestamp') or '')

    for step in phase_steps:
      phase_alias = step.get('phase_alias') or phase_key or ''
      step_title = step.get('step_title') or ''
      operator_name = step.get('operator_name') or step.get('operator_username') or ''
      timestamp = format_minute(step.get('timestamp'))

      step_data_html += f"""
        <tr>
          <td class="cell">{phase_alias}</td>
          <td class="cell">{step_title}</td>
          <td class="cell">{operator_name}</td>
          <td class="cell">{timestamp}</td>
        </tr>"""

  step_data_html += """
      </tbody>
    </table>"""

  return step_data_html


def generate_children_tables(serial_key: str) -> Tuple[str, str]:
  """Generate HTML for simple and complex children tables"""
  simple_children_table_html = ''
  complex_children_list_html = ''

  try:
    bind_vars = dict(serial_id=f'Serial/{serial_key}')
    children_result = list(db.aql.execute(Queries.GET_SERIAL_CHILDREN_FOR_DHR, bind_vars=bind_vars))

    if children_result:
      # Sort children by product code first, then serial code
      children_result.sort(key=lambda x: (x.get('product_code') or '', x.get('serial_code') or ''))

      # Separate children into simple (no data, no children) and complex (with data or children)
      simple_children = [child for child in children_result if not child.get('has_data') and not child.get('has_children')]
      complex_children = [child for child in children_result if child.get('has_data') or child.get('has_children')]

      # Create table for simple children
      if simple_children:
        simple_children_table_html = '''
        <h2>Component Serials</h2>
        <table class="table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Description</th>
              <th>S/N</th>
            </tr>
          </thead>
          <tbody>'''
        for child in simple_children:
          child_serial_code = child.get('serial_code') or ''
          child_product_code = child.get('product_code') or ''
          child_product_description = child.get('product_description') or ''
          simple_children_table_html += f'''
            <tr>
              <td class="cell">{child_product_code}</td>
              <td class="cell">{child_product_description}</td>
              <td class="cell">{child_serial_code}</td>
            </tr>'''
        simple_children_table_html += '''
          </tbody>
        </table>'''

      # Create list for complex children
      if complex_children:
        complex_children_list_html = """
        <h2>Child Serials with Detailed Data</h2>
        <p><em>The following child serials contain detailed data or sub-components. Their complete Device History Records are included on the following pages.</em></p>
        <ul>
        """
        for child in complex_children:
          child_serial_code = child.get('serial_code') or ''
          child_product_code = child.get('product_code') or ''
          child_product_description = child.get('product_description') or ''
          complex_children_list_html += f'<li><strong>{child_product_code}</strong> - {child_product_description} - {child_serial_code}</li>'
        complex_children_list_html += '</ul>'
  except Exception:
    pass

  return simple_children_table_html, complex_children_list_html





def generate_dhr_pdf(serial_key: str, include_step_data: bool = False) -> bytes:
  """Generate a DHR PDF using WeasyPrint"""
  try:
    # Fetch serial and product data
    data = fetch_dhr_data(serial_key, include_step_data)
    if not data:
      return b''

    # Generate HTML content with optimized CSS for WeasyPrint
    html_content = generate_dhr_html(serial_key, data)

    # Create PDF using WeasyPrint
    html_doc = HTML(string=html_content)
    pdf_bytes = html_doc.write_pdf()

    return pdf_bytes

  except Exception as e:
    print(f"🔍 DEBUG: Error generating DHR with WeasyPrint for serial {serial_key}: {e}")
    raise


def generate_dhr_html(serial_key: str, data: Dict[str, Any]) -> str:
  """Generate HTML content optimized for WeasyPrint DHR generation"""
  serial_info = data.get('serial') or {}
  serial_code = serial_info.get('code') or '-'
  product_code = data.get('product_code') or '-'
  product_description = data.get('product_description') or '-'
  wo_code = data.get('wo_code') or '-'
  project_code = data.get('project_code') or '-'
  created = format_date_readable(serial_info.get('created'))
  released = format_date_readable(serial_info.get('released'))
  fields = data.get('fields') or []
  step_data = data.get('step_data') or []
  wo_phase_sequence = data.get('wo_phase_sequence') or []

  # Get company information for footer
  company_info = get_company_info()
  company_name = company_info['name']
  company_logo_data_uri = ""
  if company_info['logo_path']:
    company_logo_data_uri = get_company_logo_base64(company_info['logo_path'])

  # Get current date and time for footer
  current_datetime = datetime.now().strftime('%B %d, %Y at %I:%M %p')

  # Process fields for display
  rows_html, has_serial_data = process_fields_for_display(fields, wo_phase_sequence)

  # Build serial data table HTML only if there is data
  serial_data_table_html = ''
  if has_serial_data:
    serial_data_table_html = f"""
        <h2>Serial Data</h2>
        <table class="table">
          <thead>
            <tr>
              <th>Field</th>
              <th>Value</th>
              <th>Last update</th>
              <th>User</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>"""

  # Generate step data table
  step_data_table_html = generate_step_data_table(step_data, wo_phase_sequence)

  # Generate children tables
  simple_children_table_html, complex_children_list_html = generate_children_tables(serial_key)

  html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8" />
        <style>
          @page {{
            margin: 20mm 15mm 35mm 15mm;
            size: A4;
            @bottom-left {{
              content: element(footer-left);
            }}
            @bottom-center {{
              content: element(footer-center);
            }}
            @bottom-right {{
              content: element(footer-right);
            }}
            @top-right {{
              content: element(header-right);
            }}
          }}

          @page :first {{
            @top-right {{
              content: none;
            }}
          }}
          body {{
            font-family: 'DejaVu Sans', Arial, sans-serif;
            color: #222;
            font-size: 10pt;
            line-height: 1.3;
          }}
          h1 {{
            font-size: 16pt;
            margin: 0 0 8pt 0;
            page-break-after: avoid;
          }}
          h2 {{
            font-size: 12pt;
            margin: 14pt 0 6pt 0;
            page-break-after: avoid;
          }}
          .meta {{
            margin-bottom: 10pt;
            page-break-after: avoid;
          }}
          .header-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 8pt 0 16pt 0;
            border: 1pt solid #ccc;
          }}
          .header-table th {{
            text-align: left;
            border: 1pt solid #ccc;
            padding: 4pt 6pt;
            background-color: #f0f0f0;
            font-weight: bold;
            font-size: 10pt;
            width: 25%;
          }}
          .header-table td {{
            border: 1pt solid #ccc;
            padding: 4pt 6pt;
            font-size: 10pt;
            width: 25%;
          }}
          .table {{
            width: 100%;
            border-collapse: collapse;
            margin: 8pt 0;
          }}
          .table th {{
            text-align: left;
            border-bottom: 1pt solid #ccc;
            padding: 4pt 3pt;
            background-color: #f8f8f8;
            font-weight: bold;
          }}
          .cell {{
            font-size: 8pt;
            border-bottom: 0.5pt solid #eee;
            padding: 4pt 3pt;
            vertical-align: top;
          }}
          .phase-header {{
            font-size: 8pt;
            background-color: #f6f6f6;
            border-top: 1pt solid #ccc;
            border-bottom: 1pt solid #ccc;
            padding: 6pt 3pt;
            font-weight: bold;
          }}
          .small-heading {{
            font-size: 8pt;
            margin: 12pt 0 6pt 0;
            page-break-after: avoid;
          }}
          .small-text {{
            font-size: 8pt;
            margin: 6pt 0;
          }}
          ul {{
            margin: 6pt 0;
            padding-left: 16pt;
          }}
          li {{
            font-size: 8pt;
            margin: 2pt 0;
          }}
          .table tbody tr {{
            page-break-inside: avoid;
          }}
          .table thead {{
            break-after: avoid;
          }}
          .table thead + tbody tr:first-child {{
            break-before: avoid;
          }}

          /* Footer and Header Elements */
          .footer-left {{
            position: running(footer-left);
            display: flex;
            align-items: center;
            font-size: 8pt;
          }}

          .footer-center {{
            position: running(footer-center);
            text-align: center;
            font-size: 8pt;
          }}

          .footer-center::after {{
            content: counter(page) " of " counter(pages);
          }}

          .footer-right {{
            position: running(footer-right);
            text-align: right;
            font-size: 8pt;
          }}

          .header-right {{
            position: running(header-right);
            text-align: right;
            font-size: 8pt;
            color: #666;
          }}

          .footer-logo {{
            height: 1cm;
            width: auto;
            margin-right: 5pt;
            max-width: 2cm;
          }}

          .footer-company-name {{
            font-weight: bold;
          }}
        </style>
      </head>
      <body>
        <!-- Footer Elements -->
        <div class="footer-left">
          {f'<img src="{company_logo_data_uri}" alt="Company Logo" class="footer-logo" />' if company_logo_data_uri else ''}
          <span class="footer-company-name">{company_name}</span>
        </div>

        <div class="footer-center">
          Page
        </div>

        <div class="footer-right">
          Printed on {current_datetime}
        </div>

        <!-- Header for pages after first -->
        <div class="header-right">
          {product_code} - {serial_code}
        </div>

        <h1>Device History Record</h1>
        <table class="header-table">
          <tr>
            <th>Code</th>
            <td colspan="3">{product_code}</td>
          </tr>
          <tr>
            <th>Description</th>
            <td colspan="3">{product_description}</td>
          </tr>
          <tr>
            <th>S/N</th>
            <td colspan="3">{serial_code}</td>
          </tr>
          <tr>
            <th>Work Order</th>
            <td>{wo_code}</td>
            <th>Project</th>
            <td>{project_code}</td>
          </tr>
          <tr>
            <th>Created</th>
            <td>{created}</td>
            <th>Released</th>
            <td>{released}</td>
          </tr>
        </table>
        {serial_data_table_html}
        {step_data_table_html}
        {simple_children_table_html}
        {complex_children_list_html}
      </body>
    </html>
  """

  return html


# Replace your entire process_image_attachments function with this:

# Replace your process_image_attachments function with this approach:
# Process images ONE PER PAGE to avoid page break issues

# Updated process_image_attachments function - no page numbering in footer

def process_image_attachments(image_attachments: List[Dict], serial_info_for_headers: str, wo_phase_sequence: List[str]) -> List[bytes]:
  """Process image attachments using WeasyPrint - no page numbering"""
  pdf_pages = []

  if not image_attachments:
    return pdf_pages

  print(f"🔍 DEBUG: Processing {len(image_attachments)} images with WeasyPrint (no page numbers)")

  # Group images by phase
  images_by_phase = {}
  for attachment in image_attachments:
    phase_key = attachment.get('phase_key') or None
    if phase_key not in images_by_phase:
      images_by_phase[phase_key] = []
    images_by_phase[phase_key].append(attachment)

  # Order phases by work order phase sequence
  ordered_phase_keys = []
  for k in wo_phase_sequence:
    if k in images_by_phase and k not in ordered_phase_keys:
      ordered_phase_keys.append(k)
  for k in [k for k in images_by_phase.keys() if k]:
    if k not in ordered_phase_keys:
      ordered_phase_keys.append(k)

  # Add None phase (general) at the beginning if it exists
  if None in images_by_phase:
    ordered_phase_keys.insert(0, None)

  # Process each phase group
  for phase_key in ordered_phase_keys:
    phase_images = images_by_phase[phase_key]
    if not phase_images:
      continue

    # Get phase title
    if phase_key:
      phase_title = (
        phase_images[0].get('phase_alias') or
        phase_images[0].get('phase_key') or
        phase_key or
        "Unknown Phase"
      )
    else:
      phase_title = "General"

    print(f"🔍 DEBUG: Processing {len(phase_images)} images for phase: {phase_title}")

    # Process each image individually
    for img_index, attachment in enumerate(phase_images):
      img_path = attachment['path']

      try:
        print(f"🔍 DEBUG: Creating individual page for image: {attachment['filename']}")

        # Read image data
        with open(img_path, 'rb') as imgf:
          file_data = imgf.read()
          print(f"🔍 DEBUG: Read {len(file_data)} bytes from {attachment['filename']}")
          b64 = base64.b64encode(file_data).decode('ascii')
          ext = os.path.splitext(img_path)[1].lower()
          mime = 'image/png'
          if ext == '.jpg' or ext == '.jpeg':
            mime = 'image/jpeg'
          elif ext == '.webp':
            mime = 'image/webp'
          elif ext == '.gif':
            mime = 'image/gif'
          elif ext == '.bmp':
            mime = 'image/bmp'

        # Create display name
        display_name = f"{attachment['field_label']} - {attachment['filename']}" if attachment['field_label'] else attachment['filename']

        # Create page title with correct numbering
        page_title = f"Attachments - {phase_title}"
        if len(phase_images) > 1:
          page_title += f" ({img_index + 1}/{len(phase_images)})"

        # Get company information for footer
        company_info = get_company_info()
        company_name = company_info['name']
        company_logo_data_uri = ""
        if company_info['logo_path']:
          company_logo_data_uri = get_company_logo_base64(company_info['logo_path'])

        # Get current date and time for footer
        current_datetime = datetime.now().strftime('%B %d, %Y at %I:%M %p')

        # Extract product code and serial code from serial_info_for_headers
        parts = serial_info_for_headers.split(' - ', 1)
        header_product_code = parts[0] if len(parts) >= 1 else ''
        header_serial_code = parts[1] if len(parts) >= 2 else ''

        # Create HTML for single image page - NO PAGE NUMBERING
        img_html = f"""
          <!DOCTYPE html>
          <html>
            <head>
              <meta charset='utf-8' />
              <style>
                @page {{
                  margin: 15mm 10mm 25mm 10mm;
                  size: A4;
                  @bottom-left {{
                    content: element(footer-left);
                  }}
                  @bottom-right {{
                    content: element(footer-right);
                  }}
                  @top-right {{
                    content: element(header-right);
                  }}
                }}
                body {{
                  font-family: 'DejaVu Sans', Arial, sans-serif;
                  color: #222;
                  margin: 0;
                  padding: 0;
                }}
                .header {{
                  text-align: center;
                  border-bottom: 1pt solid #ccc;
                  padding-bottom: 6pt;
                  margin-bottom: 12pt;
                  height: 50pt;
                  page-break-after: avoid;
                }}
                .header h2 {{
                  font-size: 14pt;
                  margin: 0 0 3pt 0;
                }}
                .header .serial-info {{
                  font-size: 10pt;
                  color: #666;
                  margin: 0;
                }}
                .image-container {{
                  text-align: center;
                  height: calc(257mm - 80pt);
                  position: relative;
                }}
                .filename {{
                  font-size: 11pt;
                  margin-bottom: 12pt;
                  font-weight: bold;
                  color: #333;
                  text-align: center;
                }}
                .main-image {{
                  max-width: 90%;
                  max-height: calc(257mm - 120pt);
                  width: auto;
                  height: auto;
                  display: block;
                  margin: auto;
                }}

                /* Footer Elements - NO CENTER (page numbering) */
                .footer-left {{
                  position: running(footer-left);
                  display: flex;
                  align-items: center;
                  font-size: 8pt;
                }}

                .footer-right {{
                  position: running(footer-right);
                  text-align: right;
                  font-size: 8pt;
                }}

                .header-right {{
                  position: running(header-right);
                  text-align: right;
                  font-size: 8pt;
                  color: #666;
                }}

                .footer-logo {{
                  height: 1cm;
                  width: auto;
                  margin-right: 5pt;
                  max-width: 2cm;
                }}

                .footer-company-name {{
                  font-weight: bold;
                }}
              </style>
            </head>
            <body>
              <!-- Footer Elements - NO PAGE NUMBER -->
              <div class="footer-left">
                {f'<img src="{company_logo_data_uri}" alt="Company Logo" class="footer-logo" />' if company_logo_data_uri else ''}
                <span class="footer-company-name">{company_name}</span>
              </div>

              <div class="footer-right">
                Printed on {current_datetime}
              </div>

              <!-- Header for pages after first -->
              <div class="header-right">
                {header_product_code} - {header_serial_code}
              </div>

              <div class="header">
                <h2>{page_title}</h2>
                <div class="serial-info">{serial_info_for_headers}</div>
              </div>

              <div class="image-container">
                <div class="filename">{display_name}</div>
                <img src="data:{mime};base64,{b64}"
                     alt="{display_name}"
                     class="main-image" />
              </div>
            </body>
          </html>
        """

        # Generate PDF using WeasyPrint
        html_doc = HTML(string=img_html)
        img_pdf_bytes = html_doc.write_pdf()
        pdf_pages.append(img_pdf_bytes)
        print(f"🔍 DEBUG: Successfully created PDF page for {attachment['filename']} in phase {phase_title}")

      except Exception as e:
        print(f"🔍 DEBUG: Error creating image page for {img_path}: {e}")
        continue

  return pdf_pages


def collect_attachments(fields: List[Dict], serial_key: str, include_attachments: bool) -> List[Dict]:
  """Collect file attachments from serial fields with metadata including phase information"""
  attachments: List[Dict] = []

  if not include_attachments:
    return attachments

  # print(f"🔍 DEBUG: Starting attachment collection for serial {serial_key}")
  media_root = get_config().media_path
  # print(f"🔍 DEBUG: Media root path: {media_root}")
  image_exts = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'}

  # Build a list of attachment dictionaries with metadata
  # print(f"🔍 DEBUG: Total fields to check: {len(fields)}")
  file_fields_count = 0

  for f in fields:
    field_type = (f.get('field_type') or '').lower()
    if field_type != 'files':
      continue

    file_fields_count += 1
    # print(f"🔍 DEBUG: Found file field {file_fields_count}: {f.get('label', 'N/A')}")
    form_field_key = f.get('form_field_key') or ''
    field_label = f.get('label') or ''
    phase_alias = f.get('phase_alias') or ''
    phase_key = f.get('phase_key') or ''
    # print(f"🔍 DEBUG: Form field key: '{form_field_key}', Phase: '{phase_alias}' (key: '{phase_key}'), Field: '{field_label}'")
    # print(f"🔍 DEBUG: Full field data: {f}")
    value = f.get('value')
    # print(f"🔍 DEBUG: Field value type: {type(value)}, value: {value}")

    if not value:
      print(f"🔍 DEBUG: No value in field, skipping")
      continue

    # value expected to be a list of dicts with 'name'
    try:
      if isinstance(value, list):
        print(f"🔍 DEBUG: Processing {len(value)} items in value list")
        for i, item in enumerate(value):
          filename = None
          if isinstance(item, dict):
            filename = item.get('name')
            # print(f"🔍 DEBUG: Item {i+1} is dict, filename: {filename}")
          elif isinstance(item, str):
            filename = item
            # print(f"🔍 DEBUG: Item {i+1} is string, filename: {filename}")
          else:
            # print(f"🔍 DEBUG: Item {i+1} unexpected type: {type(item)}")
            continue

          if not filename:
            print(f"🔍 DEBUG: No filename for item {i+1}, skipping")
            continue

          file_path = os.path.join(media_root, 'serial', serial_key, form_field_key, filename)
          ext = os.path.splitext(filename)[1].lower()
          file_exists = os.path.exists(file_path)

          # print(f"🔍 DEBUG: File {i+1}: {filename}")
          # print(f"🔍 DEBUG: Extension: {ext}")
          # print(f"🔍 DEBUG: Full path: {file_path}")
          # print(f"🔍 DEBUG: File exists: {file_exists}")

          if ext == '.pdf' or ext in image_exts:
            attachment_type = 'pdf' if ext == '.pdf' else 'image'
            attachment_data = {
              'path': file_path,
              'type': attachment_type,
              'filename': filename,
              'field_label': field_label,
              'phase_alias': phase_alias or 'General',  # Fallback to 'General' if phase_alias is empty
              'phase_key': phase_key
            }
            attachments.append(attachment_data)
            # print(f"🔍 DEBUG: Added {attachment_type} attachment: {filename} (Phase: '{phase_alias}' -> '{attachment_data['phase_alias']}', Field: '{field_label}')")
          else:
            print(f"🔍 DEBUG: Unsupported file type: {ext}")
      else:
        print(f"🔍 DEBUG: Value is not a list, type: {type(value)}")
    except Exception as e:
      print(f"🔍 DEBUG: Exception processing field: {e}")
      # If format is unexpected, skip
      pass

  # print(f"🔍 DEBUG: File fields found: {file_fields_count}")
  # print(f"🔍 DEBUG: Total attachments collected: {len(attachments)}")
  for i, attachment in enumerate(attachments):
    print(f"🔍 DEBUG: Attachment {i+1}: {attachment['type']} - {attachment['filename']} (Phase: {attachment['phase_alias']}, Field: {attachment['field_label']})")

  return attachments





def process_pdf_attachments(pdf_attachments: List[Dict], serial_info_for_headers: str, wo_phase_sequence: List[str]) -> List[bytes]:
  """Process PDF attachments grouped by phase and return list of processed PDF bytes"""
  processed_pdfs = []

  if not pdf_attachments:
    return processed_pdfs

  print(f"🔍 DEBUG: Processing {len(pdf_attachments)} PDFs grouped by phase")

  # Group PDFs by phase
  pdfs_by_phase = {}
  for attachment in pdf_attachments:
    phase_key = attachment.get('phase_key') or None
    if phase_key not in pdfs_by_phase:
      pdfs_by_phase[phase_key] = []
    pdfs_by_phase[phase_key].append(attachment)

  # Order phases by work order phase sequence when available
  ordered_phase_keys = []
  for k in wo_phase_sequence:
    if k in pdfs_by_phase and k not in ordered_phase_keys:
      ordered_phase_keys.append(k)
  for k in [k for k in pdfs_by_phase.keys() if k]:
    if k not in ordered_phase_keys:
      ordered_phase_keys.append(k)

  # Add None phase (general) at the beginning if it exists
  if None in pdfs_by_phase:
    ordered_phase_keys.insert(0, None)

  # Process each phase group
  for phase_key in ordered_phase_keys:
    phase_pdfs = pdfs_by_phase[phase_key]
    if not phase_pdfs:
      continue

    # Get phase title
    if phase_key:
      # Try to get a meaningful phase title with multiple fallbacks
      phase_title = (
        phase_pdfs[0].get('phase_alias') or
        phase_pdfs[0].get('phase_key') or
        phase_key or
        "Unknown Phase"
      )
    else:
      phase_title = "General"

    print(f"🔍 DEBUG: Processing {len(phase_pdfs)} PDFs for phase: {phase_title}")

    for i, attachment in enumerate(phase_pdfs):
      path_str = attachment['path']
      print(f"🔍 DEBUG: Processing PDF attachment {i+1}: {attachment['filename']} (Phase: {phase_title})")

      try:
        print(f"🔍 DEBUG: Opening PDF file: {path_str}")
        with open(path_str, 'rb') as pf:
          attach_reader = PdfReader(pf)
          num_pages = len(attach_reader.pages)
          print(f"🔍 DEBUG: PDF has {num_pages} pages")

          # Create a new writer for this PDF with headers
          writer = PdfWriter()

          # Draw each original page inside a framed area on A4 with header
          page_width, page_height = A4
          left_margin = 15 * mm
          right_margin = 15 * mm
          bottom_margin = 15 * mm
          top_margin = 20 * mm  # Reduced from 35mm to 20mm for more space
          header_area = 18 * mm  # Reduced from 28mm to 18mm for more space
          frame_left = float(left_margin)
          frame_bottom = float(bottom_margin)
          frame_right = float(page_width - right_margin)
          frame_top = float(page_height - (top_margin + header_area))
          frame_width = frame_right - frame_left
          frame_height = frame_top - frame_bottom

          filename = attachment['filename']
          field_label = attachment['field_label']

          for idx, original_page in enumerate(attach_reader.pages):
            # Create overlay with header and border
            overlay_buf = io.BytesIO()
            c = canvas.Canvas(overlay_buf, pagesize=A4)

            # Draw 3-line header with better spacing
            header_y_line1 = float(page_height - top_margin - 6)
            header_y_line2 = float(page_height - top_margin - 18)
            header_y_line3 = float(page_height - top_margin - 30)

            c.setFont("Helvetica-Bold", 16)
            c.drawString(float(left_margin), header_y_line1, f"Attachments - {phase_title}")
            c.setFont("Helvetica", 12)
            c.drawString(float(left_margin), header_y_line2, f"{serial_info_for_headers}")

            # Draw field label and filename info
            if field_label:
              c.setFont("Helvetica", 10)
              c.drawString(float(left_margin), header_y_line3, f"Field: {field_label}")

            # Draw filename and page number on the right
            c.setFont("Helvetica", 9)
            filename_text = f"{filename} - Page {idx+1}/{num_pages}"
            text_width = c.stringWidth(filename_text)
            c.drawString(float(frame_right - text_width), header_y_line3, filename_text)

            # Draw border around content area
            c.setLineWidth(1)
            c.rect(frame_left, frame_bottom, frame_width, frame_height, stroke=1, fill=0)
            c.showPage()
            c.save()
            overlay_buf.seek(0)
            overlay_reader = PdfReader(overlay_buf)
            overlay_page = overlay_reader.pages[0]

            # Fit original page inside frame while preserving aspect
            orig_w = float(original_page.mediabox.width)
            orig_h = float(original_page.mediabox.height)
            scale = min(frame_width / orig_w, frame_height / orig_h)
            scaled_w = orig_w * scale
            scaled_h = orig_h * scale
            translate_x = frame_left + (frame_width - scaled_w) / 2
            translate_y = frame_bottom + (frame_height - scaled_h) / 2

            transformation = Transformation().scale(scale).translate(tx=translate_x, ty=translate_y)
            overlay_page.merge_transformed_page(original_page, transformation)
            writer.add_page(overlay_page)

          # Convert writer to bytes
          output = io.BytesIO()
          writer.write(output)
          output.seek(0)
          processed_pdfs.append(output.getvalue())
          print(f"🔍 DEBUG: Successfully processed PDF {filename} with {num_pages} pages for phase {phase_title}")

      except Exception as e:
        print(f"🔍 DEBUG: Error processing PDF {path_str}: {e}")
        continue

  return processed_pdfs


def generate_dhr_for_serial(serial_key: str, include_attachments: bool = False, include_step_data: bool = False) -> bytes:
  """Generate a DHR PDF for a specific serial using WeasyPrint"""
  try:

    # Fetch data once and generate main DHR
    data = fetch_dhr_data(serial_key, include_step_data)
    if not data:
      return b''

    # Generate main DHR HTML and PDF
    html_content = generate_dhr_html(serial_key, data)
    html_doc = HTML(string=html_content)
    main_pdf_bytes = html_doc.write_pdf()

    if not main_pdf_bytes:
      return b''

    # If no attachments requested, return the main PDF
    if not include_attachments:
      return main_pdf_bytes

    # Create a PDF writer to combine main content with attachments

    writer = PdfWriter()
    main_reader = PdfReader(io.BytesIO(main_pdf_bytes))
    for pg in main_reader.pages:
      writer.add_page(pg)

    # Use the already fetched data for attachment processing
    fields = data.get('fields', [])
    attachments = collect_attachments(fields, serial_key, include_attachments)

    if not attachments:
      # print(f"🔍 DEBUG: No attachments to process")
      return main_pdf_bytes

    # Get serial info for attachment headers from existing data
    serial_info = data.get('serial') or {}
    product_code = data.get('product_code') or ''
    serial_code = serial_info.get('code') or ''
    serial_info_for_headers = f"{product_code} - {serial_code}" if product_code and serial_code else serial_key
    wo_phase_sequence = data.get('wo_phase_sequence', [])

    # Separate image and PDF attachments
    image_attachments = [attachment for attachment in attachments if attachment['type'] == 'image']
    pdf_attachments = [attachment for attachment in attachments if attachment['type'] == 'pdf']

    # Process image attachments with WeasyPrint
    if image_attachments:
      image_pdf_pages = process_image_attachments(image_attachments, serial_info_for_headers, wo_phase_sequence)
      for img_pdf_bytes in image_pdf_pages:
        img_reader = PdfReader(io.BytesIO(img_pdf_bytes))
        for pg in img_reader.pages:
          writer.add_page(pg)

    # Process PDF attachments (keep using ReportLab)
    if pdf_attachments:
      processed_pdf_bytes_list = process_pdf_attachments(pdf_attachments, serial_info_for_headers, wo_phase_sequence)
      for pdf_bytes in processed_pdf_bytes_list:
        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        for pg in pdf_reader.pages:
          writer.add_page(pg)

    # Return combined PDF
    total_pages = len(writer.pages)
    # print(f"🔍 DEBUG: Final PDF has {total_pages} total pages")
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    final_size = len(output.getvalue())
    # print(f"🔍 DEBUG: Final PDF size: {final_size} bytes")

    return output.getvalue()

  except Exception as e:
    print(f"🔍 DEBUG: Error generating DHR with WeasyPrint for serial {serial_key}: {e}")
    raise





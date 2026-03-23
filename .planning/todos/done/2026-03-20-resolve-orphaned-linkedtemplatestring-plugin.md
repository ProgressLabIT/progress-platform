---
created: 2026-03-20T23:06:16.419Z
title: Resolve orphaned linkedTemplateString plugin
area: ui
files:
  - webapps/main/src/lib/print/plugins/linkedTemplateString.js
  - webapps/main/src/lib/print/plugins/index.js
---

## Problem

`linkedTemplateString.js` exists as a pdfme plugin factory (createLinkedTemplateString) but is not registered in `buildPlugins()` in `index.js` and is not imported anywhere in production code — only in its own test file. The template_expression feature was implemented via a `linkType` option in `linkConfig.js` instead, making this file an architectural orphan.

If a field is ever saved with `type: 'template_string'`, pdfme cannot render it since the plugin is not registered.

## Solution

Two options:
1. **Register it**: Import `createLinkedTemplateString` in `index.js` and add `template_string: createLinkedTemplateString()` to `buildPlugins()`. Aligns with original TMPL-03 requirement.
2. **Delete it**: Remove `linkedTemplateString.js` and its test if the linkConfig.js approach is the accepted final architecture. Update REQUIREMENTS.md to reflect the architectural deviation.

Decide which approach fits the intended UX — dedicated plugin type vs linkType on text fields.

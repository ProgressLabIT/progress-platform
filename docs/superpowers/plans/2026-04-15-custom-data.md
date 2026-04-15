# CustomData Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `CustomData` ArangoDB collection with full CRUD backend + admin UI so Prefect flows and reports can be configured from the main webapp instead of the Prefect UI.

**Architecture:** New endpoint file for direct CRUD (no events), new Vue library view with master-detail layout reusing the existing `JsonEditor.vue` component for value editing. Collection added to both production and test DB init scripts.

**Tech Stack:** FastAPI, python-arango, ArangoDB, Vue 3 Composition API, Quasar, CodeMirror 6 (via existing JsonEditor.vue)

**Spec:** `docs/superpowers/specs/2026-04-15-custom-data-design.md`

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `backend/api/models/custom_data.py` | Pydantic model for CustomData documents |
| Create | `backend/api/endpoints/custom_data.py` | CRUD endpoints for CustomData |
| Modify | `backend/api/endpoints/__init__.py` | Export custom_data router |
| Modify | `backend/api/main.py` | Register custom_data router |
| Modify | `deploy/scripts/db_init.py` | Add CustomData collection |
| Modify | `testing/pytest/conftest_helpers/schema.py` | Add CustomData collection to test schema |
| Create | `webapps/main/src/views/CustomDataLibrary.vue` | Master-detail admin view |
| Create | `webapps/main/src/views/CustomDataDetail.vue` | Detail/edit panel for a single record |
| Modify | `webapps/main/src/router/adminRoutes.js` | Add customDataLibrary route |
| Modify | `webapps/main/src/views/AdminSection.vue` | Add tab to adminViews array |
| Modify | `webapps/main/src/i18n/en.js` | Add translation key |

---

### Task 1: Backend Model

**Files:**
- Create: `backend/api/models/custom_data.py`

- [ ] **Step 1: Create the CustomData model**

```python
import re
from typing import Any

from pydantic import field_validator

from models.base_models import ArangoDocument

KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')
KEY_MAX_LENGTH = 64


class CustomData(ArangoDocument):
    value: Any
    description: str | None = None

    @field_validator('key', mode='before', check_fields=False)
    @classmethod
    def validate_key(cls, v):
        if v is not None:
            if not KEY_PATTERN.match(v):
                raise ValueError(
                    'Key must start with a lowercase letter and contain only lowercase letters, digits, and underscores'
                )
            if len(v) > KEY_MAX_LENGTH:
                raise ValueError(f'Key must be at most {KEY_MAX_LENGTH} characters')
        return v
```

Note: The `key` field is inherited from `ArangoDocument` as `key: str | None = Field(None, alias="_key")`. The validator targets the field name `key` (not the alias `_key`). `check_fields=False` is needed because the field is inherited.

- [ ] **Step 2: Commit**

```bash
git add backend/api/models/custom_data.py
git commit -m "feat: add CustomData pydantic model with key validation"
```

---

### Task 2: Backend Endpoints

**Files:**
- Create: `backend/api/endpoints/custom_data.py`
- Modify: `backend/api/endpoints/__init__.py:1-21`
- Modify: `backend/api/main.py:59-78`

- [ ] **Step 1: Create the endpoint file**

```python
import re
import traceback

from fastapi import APIRouter, HTTPException, Depends, Query
from utils import auth
from utils.api import APIResponse
from models.custom_data import CustomData, KEY_PATTERN, KEY_MAX_LENGTH
from utils.db import db

router = APIRouter()

COLLECTION = 'CustomData'


def _validate_key(key: str):
    """Validate _key format. Raises 422 if invalid."""
    if not KEY_PATTERN.match(key) or len(key) > KEY_MAX_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=f'Key must match {KEY_PATTERN.pattern} and be at most {KEY_MAX_LENGTH} chars',
        )


@router.get('/custom-data',
    dependencies=[Depends(auth.verify_token)])
def list_custom_data(search: str | None = None):
    query = """
        FOR d IN CustomData
        FILTER @search == null
            OR CONTAINS(LOWER(d._key), LOWER(@search))
            OR CONTAINS(LOWER(d.description || ''), LOWER(@search))
        SORT d._key
        RETURN d
    """
    cursor = db.aql.execute(query, bind_vars=dict(search=search))
    return [CustomData(**d) for d in cursor]


@router.get('/custom-data/{key}',
    dependencies=[Depends(auth.verify_token)])
def get_custom_data(key: str):
    doc = db.collection(COLLECTION).get(key)
    if not doc:
        raise HTTPException(status_code=404, detail=f'CustomData {key!r} not found')
    return CustomData(**doc)


@router.put('/custom-data/{key}',
    dependencies=[Depends(auth.verify_token)])
def upsert_custom_data(key: str, body: CustomData):
    _validate_key(key)
    doc = body.model_dump(by_alias=True, exclude_none=True)
    doc['_key'] = key

    collection = db.collection(COLLECTION)
    existing = collection.get(key)

    try:
        if existing:
            collection.replace(doc, check_rev=False)
            message = f'CustomData {key!r} updated'
        else:
            collection.insert(doc)
            message = f'CustomData {key!r} created'
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())

    return APIResponse(message=message, detail=dict(_key=key))


@router.delete('/custom-data/{key}',
    dependencies=[Depends(auth.verify_token)])
def delete_custom_data(key: str):
    collection = db.collection(COLLECTION)
    if not collection.get(key):
        raise HTTPException(status_code=404, detail=f'CustomData {key!r} not found')

    try:
        collection.delete(key)
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())

    return APIResponse(message=f'CustomData {key!r} deleted')
```

- [ ] **Step 2: Register the router in endpoints/__init__.py**

Add this line to `backend/api/endpoints/__init__.py` after the existing imports:

```python
from .custom_data import router as custom_data
```

- [ ] **Step 3: Mount the router in main.py**

Add this line in `backend/api/main.py` among the `app.include_router(...)` calls (after `endpoints.config`):

```python
app.include_router(endpoints.custom_data, tags=['Administration'])
```

- [ ] **Step 4: Commit**

```bash
git add backend/api/endpoints/custom_data.py backend/api/endpoints/__init__.py backend/api/main.py
git commit -m "feat: add CustomData CRUD endpoints"
```

---

### Task 3: Database Init Scripts

**Files:**
- Modify: `deploy/scripts/db_init.py:238-240` (near CustomListValue)
- Modify: `testing/pytest/conftest_helpers/schema.py:20+` (COLLECTIONS list)

- [ ] **Step 1: Add collection to production db_init.py**

In `deploy/scripts/db_init.py`, add this entry to the collections list right before the `CustomListValue` entry (around line 238):

```python
  Collection(name='CustomData'),
```

- [ ] **Step 2: Add collection to test schema**

In `testing/pytest/conftest_helpers/schema.py`, add the same entry to the `COLLECTIONS` list, maintaining alphabetical order among the uppercase-starting entries:

```python
    Collection(name='CustomData'),
```

- [ ] **Step 3: Commit**

```bash
git add deploy/scripts/db_init.py testing/pytest/conftest_helpers/schema.py
git commit -m "feat: add CustomData collection to db init scripts"
```

---

### Task 4: Frontend — CustomDataDetail Component

**Files:**
- Create: `webapps/main/src/views/CustomDataDetail.vue`

- [ ] **Step 1: Create the detail/edit component**

This is the right panel that shows when a record is selected or when creating new.

```vue
<template>
  <div class="q-pa-md column full-height">
    <div class="text-h6 q-mb-md">
      {{ isNew ? $t('new') : record_key }}
    </div>

    <!-- Key (editable only on create) -->
    <q-input
      v-if="isNew"
      v-model="form.key"
      dense
      filled
      class="q-mb-md"
      label="Key"
      :rules="[validateKey]"
      :hint="`a-z, 0-9, _ — max ${KEY_MAX_LENGTH} chars`"
      lazy-rules
    />

    <!-- Description -->
    <q-input
      v-model="form.description"
      dense
      filled
      class="q-mb-md"
      :label="$t('description')"
      type="textarea"
      autogrow
    />

    <!-- JSON Value -->
    <div class="col" style="min-height: 200px">
      <JsonEditor
        v-model="form.value_str"
        label="Value (JSON)"
        :rows="15"
        @validation-error="json_has_error = $event"
      />
    </div>

    <!-- Actions -->
    <div class="row q-mt-md q-gutter-sm">
      <q-btn
        color="theme-blue"
        :label="$t('save')"
        :disable="!canSave"
        :loading="saving"
        @click="save"
      />
      <q-space />
      <q-btn
        v-if="!isNew"
        flat
        color="negative"
        :label="$t('delete')"
        @click="confirmDelete"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { api } from '@/boot/axios.js';
import JsonEditor from '@/components/JsonEditor.vue';

const KEY_PATTERN = /^[a-z][a-z0-9_]*$/;
const KEY_MAX_LENGTH = 64;

const props = defineProps({
  record: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(['reload']);

const router = useRouter();
const $q = useQuasar();

const isNew = computed(() => !props.record);

const form = ref({
  key: '',
  description: '',
  value_str: '{}',
});

const json_has_error = ref(false);
const saving = ref(false);

// Populate form when record changes
watch(
  () => props.record,
  (rec) => {
    if (rec) {
      form.value = {
        key: rec._key,
        description: rec.description || '',
        value_str: JSON.stringify(rec.value, null, 2),
      };
    } else {
      form.value = { key: '', description: '', value_str: '{}' };
    }
  },
  { immediate: true },
);

function validateKey(val) {
  if (!val) return 'Key is required';
  if (val.length > KEY_MAX_LENGTH) return `Max ${KEY_MAX_LENGTH} characters`;
  if (!KEY_PATTERN.test(val)) return 'Lowercase letters, digits, underscores only. Must start with a letter.';
  return true;
}

const canSave = computed(() => {
  if (json_has_error.value) return false;
  if (isNew.value && validateKey(form.value.key) !== true) return false;
  return true;
});

async function save() {
  const key = isNew.value ? form.value.key : props.record._key;
  saving.value = true;

  try {
    const payload = {
      value: JSON.parse(form.value.value_str),
      description: form.value.description || null,
    };
    await api.put(`custom-data/${key}`, payload);

    $q.notify({ type: 'positive', message: `Saved ${key}` });
    emit('reload');

    if (isNew.value) {
      router.push({ name: 'customDataDetail', params: { data_key: key } });
    }
  } catch (e) {
    $q.notify({ type: 'negative', message: e.response?.data?.detail || e.message });
  } finally {
    saving.value = false;
  }
}

function confirmDelete() {
  $q.dialog({
    title: 'Delete',
    message: `Delete "${props.record._key}"?`,
    cancel: true,
    persistent: true,
  }).onOk(async () => {
    try {
      await api.delete(`custom-data/${props.record._key}`);
      $q.notify({ type: 'positive', message: 'Deleted' });
      emit('reload');
      router.push({ name: 'customDataLibrary' });
    } catch (e) {
      $q.notify({ type: 'negative', message: e.response?.data?.detail || e.message });
    }
  });
}
</script>
```

- [ ] **Step 2: Commit**

```bash
git add webapps/main/src/views/CustomDataDetail.vue
git commit -m "feat: add CustomDataDetail view component"
```

---

### Task 5: Frontend — CustomDataLibrary Component

**Files:**
- Create: `webapps/main/src/views/CustomDataLibrary.vue`

- [ ] **Step 1: Create the master-detail list component**

```vue
<template>
  <q-splitter v-model="splitter_model" class="absolute-full">
    <template #before>
      <div class="full-height column">
        <q-input
          v-model="search_text"
          dense
          filled
          class="q-px-md q-pt-md"
          :placeholder="$capitalize($t('search'))"
        >
          <template #append>
            <q-icon name="mdi-magnify" />
          </template>
        </q-input>

        <div
          class="row q-mt-md q-px-lg q-py-sm text-h6 text-uppercase weight-bold"
        >
          <div class="col">
            Key
          </div>
        </div>

        <q-separator />

        <q-scroll-area class="col">
          <div
            v-for="(item, index) in filtered_items"
            :key="item._key"
            class="row pointer q-px-lg q-py-xs medium overflow-hidden"
            :class="{
              'alternate-row': index % 2 === 0,
              'bg-blue-backdrop': item._key === selected_key,
            }"
            @click="showDetail(item._key)"
          >
            <div class="col ellipsis">
              {{ item._key }}
            </div>
            <div class="col ellipsis text-caption text-grey">
              {{ item.description }}
            </div>
          </div>
        </q-scroll-area>

        <q-separator />

        <div class="row flex-center smaller q-py-xs">
          {{ filtered_items.length }} {{ $t('of') }} {{ items.length }}
        </div>

        <div class="q-pa-md q-mt-auto">
          <q-btn
            class="full-width q-mt-auto"
            color="theme-blue"
            :label="$t('new')"
            @click="showNew"
          />
        </div>
      </div>
    </template>

    <template #after>
      <div class="col full-height">
        <router-view v-slot="{ Component, route }">
          <component
            :is="Component"
            v-if="route.name === 'customDataNew'"
            @reload="loadItems"
          />
          <component
            :is="Component"
            v-else-if="selected_record"
            :record="selected_record"
            @reload="loadItems"
          />
        </router-view>
      </div>
    </template>
  </q-splitter>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { api } from '@/boot/axios.js';
import multiMatch from '@/lib/MultiFieldSearch.js';

const route = useRoute();
const router = useRouter();

const search_text = ref(undefined);
const splitter_model = ref(30);
const items = ref([]);

const selected_key = computed(() => route.params.data_key);

const selected_record = computed(() => {
  const key = selected_key.value;
  if (!key) return undefined;
  return items.value.find((item) => item._key === key);
});

const filtered_items = computed(() => {
  return items.value.filter((item) =>
    multiMatch(search_text.value, item, ['_key', 'description']),
  );
});

async function loadItems() {
  try {
    const { data } = await api.get('custom-data');
    items.value = data;
  } catch (e) {
    items.value = [];
  }
}

function showDetail(data_key) {
  router.push({ name: 'customDataDetail', params: { data_key } });
}

function showNew() {
  router.push({ name: 'customDataNew' });
}

onMounted(loadItems);
</script>
```

- [ ] **Step 2: Commit**

```bash
git add webapps/main/src/views/CustomDataLibrary.vue
git commit -m "feat: add CustomDataLibrary master-detail view"
```

---

### Task 6: Frontend — Routing, Admin Tab, i18n

**Files:**
- Modify: `webapps/main/src/router/adminRoutes.js:177-182` (after counterLibrary)
- Modify: `webapps/main/src/views/AdminSection.vue:34-43`
- Modify: `webapps/main/src/i18n/en.js:1092-1137`

- [ ] **Step 1: Add route in adminRoutes.js**

In `webapps/main/src/router/adminRoutes.js`, add this entry after the `counterLibrary` block (after line 177) and before the `flowLibrary` block:

```javascript
      {
        path: 'custom-data',
        name: 'customDataLibrary',
        component: () => import('@/views/CustomDataLibrary.vue'),
        children: [
          {
            path: ':data_key',
            name: 'customDataDetail',
            component: () => import('@/views/CustomDataDetail.vue'),
            props: true,
          },
          {
            path: 'new',
            name: 'customDataNew',
            component: () => import('@/views/CustomDataDetail.vue'),
          },
        ],
      },
```

- [ ] **Step 2: Add tab in AdminSection.vue**

In `webapps/main/src/views/AdminSection.vue`, add `'customDataLibrary'` to the `adminViews` array, after `'counterLibrary'` and before `'flowLibrary'`:

```javascript
const adminViews = [
  'generalSettings',
  'userLibrary',
  'operationLibrary',
  'issueTypeLibrary',
  'taskTypeLibrary',
  'formFieldLibrary',
  'counterLibrary',
  'customDataLibrary',
  'flowLibrary',
];
```

- [ ] **Step 3: Add i18n translation**

In `webapps/main/src/i18n/en.js`, add this entry in the `views` object (after `counterLibrary` on line 1101):

```javascript
    customDataLibrary: 'Custom data',
```

- [ ] **Step 4: Commit**

```bash
git add webapps/main/src/router/adminRoutes.js webapps/main/src/views/AdminSection.vue webapps/main/src/i18n/en.js
git commit -m "feat: wire CustomData into admin routing, tabs, and i18n"
```

---

### Task 7: Manual Verification

- [ ] **Step 1: Start the dev server**

```bash
cd webapps/main && yarn dev
```

- [ ] **Step 2: Verify the following in the browser**

1. Navigate to Admin → "Custom data" tab appears between "Counters" and "Data flows"
2. Click "Custom data" — empty list shows "0 of 0"
3. Click "New" — detail panel shows key input, description textarea, JSON editor
4. Type an invalid key (e.g., `123bad`) — validation error shows inline
5. Type a valid key (e.g., `my_threshold`) — validation passes
6. Enter JSON value `{"limit": 42, "enabled": true}` — editor highlights syntax
7. Click Save — record appears in list
8. Click the record — detail panel shows key as read-only, description and value editable
9. Edit value and save — changes persist on reload
10. Click Delete → confirm — record removed from list

- [ ] **Step 3: Test API directly**

```bash
# List (empty)
curl -s http://localhost:8000/custom-data -H "Authorization: Bearer $TOKEN" | python -m json.tool

# Create
curl -s -X PUT http://localhost:8000/custom-data/test_record \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": {"foo": "bar"}, "description": "test"}' | python -m json.tool

# Get
curl -s http://localhost:8000/custom-data/test_record -H "Authorization: Bearer $TOKEN" | python -m json.tool

# Invalid key (should 422)
curl -s -X PUT http://localhost:8000/custom-data/BAD-KEY \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": 1}' | python -m json.tool

# Delete
curl -s -X DELETE http://localhost:8000/custom-data/test_record -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

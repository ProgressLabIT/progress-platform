<template>
  <div class="json-editor-wrapper">
    <div v-if="label" class="json-editor-header row items-center justify-between q-mb-sm text-weight-medium">
      {{ label }}
    </div>
    <div ref="editorRef" class="json-editor-container" :class="{ 'has-error': hasError }"></div>
    <div v-if="hasError" class="text-theme-red text-body2 q-mt-sm">
      {{ $t('json_syntax_error') }}
    </div>
    <q-btn
        v-if="!hasError"
        outline
        dense
        size="sm"
        padding="sm"
        color="theme-blue"
        class="full-width q-mt-sm"
        :label="$t('format_json')"
        icon="mdi-code-json"
        @click="formatJson"
      />
  </div>
</template>

<script setup>
import { defaultKeymap } from '@codemirror/commands';
import { json, jsonParseLinter } from '@codemirror/lang-json';
import { syntaxHighlighting, HighlightStyle } from '@codemirror/language';
import { linter, lintGutter } from '@codemirror/lint';
import { EditorState } from '@codemirror/state';
import { EditorView, keymap } from '@codemirror/view';
import { tags } from '@lezer/highlight';
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  label: {
    type: String,
    default: '',
  },
  rows: {
    type: Number,
    default: 10,
  },
});

const emit = defineEmits(['update:modelValue', 'validationError']);

const editorRef = ref(null);
const hasError = ref(false);
let editorView = null;

// Syntax highlighting colors for JSON
const jsonHighlightStyle = HighlightStyle.define([
  { tag: tags.propertyName, color: '#9cdcfe' }, // Property names (keys) in blue
  { tag: tags.string, color: '#ce9178' }, // String values in orange
  { tag: tags.number, color: '#b5cea8' }, // Numbers in light green
  { tag: tags.bool, color: '#569cd6' }, // Booleans in blue
  { tag: tags.null, color: '#569cd6' }, // Null in blue
  { tag: tags.punctuation, color: '#d4d4d4' }, // Punctuation (brackets, colons) in grey
  { tag: tags.brace, color: '#ffd700' }, // Braces in gold
]);

// Custom theme to match Quasar styles
const customTheme = EditorView.theme({
  '&': {
    backgroundColor: 'var(--q-dark, #1e1e1e)',
    color: 'var(--q-color-text, #e0e0e0)',
    border: '1px solid var(--q-color-separator, #424242)',
    borderRadius: '4px',
    fontSize: '14px',
    fontFamily: 'monospace',
    width: '100%',
    height: '100%',
  },
  '.cm-scroller': {
    overflow: 'auto !important',
  },
  '.cm-content': {
    caretColor: 'var(--q-color-primary, #2196f3)',
    padding: '8px 0',
    minHeight: `${props.rows * 1.5}em`,
  },
  '.cm-line': {
    padding: '0 8px',
  },
  '&.cm-focused': {
    outline: '2px solid var(--q-color-primary, #2196f3)',
    outlineOffset: '-1px',
  },
  '.cm-gutters': {
    backgroundColor: 'var(--q-dark, #2d2d2d)',
    color: 'var(--q-color-text-secondary, #9e9e9e)',
    border: 'none',
  },
  '.cm-activeLineGutter': {
    backgroundColor: 'var(--q-dark, #3d3d3d)',
  },
  '.cm-selectionBackground, ::selection': {
    backgroundColor: 'var(--q-color-primary, #2196f3) !important',
    opacity: '0.3',
  },
  '.cm-cursor': {
    borderLeftColor: 'var(--q-color-primary, #2196f3)',
  },
  // Error styling
  '&.has-error': {
    borderColor: 'var(--q-color-negative, #f44336)',
  },
  '.cm-lintRange-error': {
    backgroundImage: 'none',
    textDecoration: 'underline wavy var(--q-color-negative, #f44336)',
  },
  '.cm-diagnostic-error': {
    borderLeftColor: 'var(--q-color-negative, #f44336)',
  },
});

// Validation function
const validateJson = (content) => {
  if (!content.trim()) {
    hasError.value = false;
    emit('validationError', false);
    return true;
  }

  try {
    JSON.parse(content);
    hasError.value = false;
    emit('validationError', false);
    return true;
  } catch (e) {
    hasError.value = true;
    emit('validationError', true);
    return false;
  }
};

// Format JSON
const formatJson = () => {
  if (!editorView) {
    return;
  }

  const currentValue = editorView.state.doc.toString();
  try {
    const parsed = JSON.parse(currentValue);
    const formatted = JSON.stringify(parsed, null, 2);

    editorView.dispatch({
      changes: {
        from: 0,
        to: editorView.state.doc.length,
        insert: formatted,
      },
    });

    emit('update:modelValue', formatted);
  } catch (e) {
    // If JSON is invalid, do nothing
  }
};

// Initialize CodeMirror
const initEditor = () => {
  if (!editorRef.value || editorView) {
    return;
  }

  const startState = EditorState.create({
    doc: props.modelValue || '',
    extensions: [
      json(),
      linter(jsonParseLinter()),
      lintGutter(),
      syntaxHighlighting(jsonHighlightStyle),
      customTheme,
      keymap.of(defaultKeymap),
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          const newValue = update.state.doc.toString();
          validateJson(newValue);
          emit('update:modelValue', newValue);
        }
      }),
    ],
  });

  editorView = new EditorView({
    state: startState,
    parent: editorRef.value,
  });

  // Initial validation
  validateJson(props.modelValue || '');
};

// Watch for external changes to modelValue
watch(
  () => props.modelValue,
  (newValue) => {
    if (!editorView) {
      return;
    }

    const currentValue = editorView.state.doc.toString();
    if (newValue !== currentValue) {
      editorView.dispatch({
        changes: {
          from: 0,
          to: editorView.state.doc.length,
          insert: newValue || '',
        },
      });
      validateJson(newValue || '');
    }
  }
);

onMounted(async () => {
  await nextTick();
  initEditor();

  // Ensure the editor syncs with the latest prop value after mount
  // This handles the case where the prop was updated before mounting completed
  await nextTick();
  if (editorView && props.modelValue !== undefined) {
    const currentValue = editorView.state.doc.toString();
    if (props.modelValue !== currentValue) {
      editorView.dispatch({
        changes: {
          from: 0,
          to: editorView.state.doc.length,
          insert: props.modelValue || '',
        },
      });
      validateJson(props.modelValue || '');
    }
  }
});

onBeforeUnmount(() => {
  if (editorView) {
    editorView.destroy();
    editorView = null;
  }
});
</script>

<style scoped>
.json-editor-wrapper {
  min-width: 300px;
  max-width: 60vw;
  display: flex;
  flex-direction: column;
}

.json-editor-container {
  max-height: 600px;
  max-width: 100%;
  overflow: auto;
  position: relative;
}

.json-editor-container.has-error {
  border-color: var(--q-color-negative) !important;
}

.json-editor-header {
  min-height: 32px;
}
</style>


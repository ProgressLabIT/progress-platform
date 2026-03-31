<template>
  <BaseDialog
    :show="show"
    :no-backdrop-dismiss="false"
    @keyup.enter="update"
    @close="$emit('close')"
  >
    <q-card class="surface2 q-pa-md" :style="`width: ${width}`">
      <q-card-section>
        <div class="text-h4 display highlight text-uppercase">
          {{ prompt ?? $t('update') }}
        </div>

        <div v-if="helpText" class="text-body2 q-mt-sm">
          {{ helpText }}
        </div>

        <q-input
          v-if="input_type !== 'number'"
          v-model="value"
          autofocus
          filled
          autogrow
          class="q-mt-md"
          input-class="text-body1"
          hide-bottom-space
          type="text"
          @keyup.enter="update"
        />
        <q-input
          v-if="input_type === 'number'"
          v-model.number="value"
          autofocus
          filled
          class="q-mt-md"
          input-class="text-body1"
          hide-bottom-space
          type="number"
          :max="max"
          :min="min"
          @keyup.enter="update"
        />
      </q-card-section>

      <q-card-actions align="between">
        <q-btn
          size="12px"
          flat
          color="theme-grey"
          :label="$t('cancel')"
          @click="$emit('close')"
        />
        <q-btn
          v-if="parsedValue != initial_value"
          size="12px"
          flat
          color="theme-blue"
          :label="$t(confirmLabel)"
          @click="update"
        />
      </q-card-actions>
    </q-card>
  </BaseDialog>
</template>

<script>
import BaseDialog from '@/components/BaseDialog.vue';
export default {
  name: 'BasePrompt',

  components: {
    BaseDialog,
  },

  props: {
    show: {
      type: Boolean,
      default: true,
    },
    width: {
      type: String,
      default: '300px',
    },
    prompt: {
      type: String,
      default: undefined,
    },
    helpText: {
      type: String,
      default: undefined,
    },
    input_type: {
      type: String,
      default: 'text',
    },
    initial_value: {
      type: [String, Number, null],
      required: true,
    },
    max: {
      type: Number,
      default: null,
    },
    min: {
      type: Number,
      default: null,
    },
    confirmLabel: {
      type: String,
      default: 'save',
    },
  },

  emits: ['close', 'update'],

  data() {
    return {
      value: null,
    };
  },

  updated() {
    this.value = this.initial_value;
  },

  computed: {
    parsedValue() {
      if (this.input_type === 'number' && this.value !== '' && this.value !== null) {
        return Number(this.value);
      }
      return this.value;
    },
  },

  methods: {
    update(event) {
        this.$emit('update', this.parsedValue);
    },
  },
};
</script>

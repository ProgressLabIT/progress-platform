<template>
  <BaseDialog :show="show" :no-backdrop-dismiss="false" @keyup.enter="update">
    <q-card class="surface2 q-pa-md" :style="`width: ${width}`">
      <q-card-section>
        <div class="text-h4 display highlight text-uppercase">
          {{ prompt ?? $t('update') }}
        </div>

        <q-input
          v-model="value"
          autofocus
          filled
          autogrow
          class="q-mt-md"
          input-class="text-body1"
          hide-bottom-space
          :type="input_type"
          :max="max"
          :min="min"
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
          v-if="/* eslint-disable-line vue/eqeqeq */ value != initial_value"
          size="12px"
          flat
          color="theme-blue"
          :label="$t('save')"
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

  methods: {
    update() {
      this.$emit('update', this.value);
    },
  },
};
</script>

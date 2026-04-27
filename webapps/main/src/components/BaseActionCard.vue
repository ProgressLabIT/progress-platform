<template>
  <q-card class="surface2 q-pa-md" style="min-width: 400px; max-height: 80vh;">
    <slot name="title">
      <q-card-section v-if="title">
        <div class="text-h3 display highlight">
          {{ title }}
        </div>
      </q-card-section>
    </slot>

    <q-card-section>
      <slot></slot>
    </q-card-section>

    <q-card-section class="row justify-between">
      <slot name="actions">
        <q-btn :color="saveColor" @click="$emit('save')">
          {{ saveLabel ?? $t('save') }}
        </q-btn>
        <q-btn :color="cancelColor" @click="$emit('cancel')">
          {{ cancelLabel ?? $t('cancel') }}
        </q-btn>
      </slot>
    </q-card-section>
  </q-card>
</template>

<script>
export default {
  name: 'BaseActionCard',

  props: {
    title: {
      type: String,
      default: undefined,
    },
    saveLabel: {
      type: String,
      default: undefined,
    },
    cancelLabel: {
      type: String,
      default: undefined,
    },
    saveColor: {
      type: String,
      default: 'theme-blue',
    },
    cancelColor: {
      type: String,
      default: 'theme-grey',
    },
  },
  emits: ['save', 'cancel'],
};
</script>

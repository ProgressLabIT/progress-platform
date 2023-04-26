<template>
  <div>
    <!-- TEXT -->
    <q-input
      v-if="field_data.type == 'text'"
      filled
      stack-label
      autogrow
      lazy-rules
      :disable="disable"
      :dense="dense"
      :label="field_data.label"
      :hint="field_data.hint"
      :model-value="field_data.value"
      :rules="[value => (field_data.required ? !!value : true) || $t('field_required_alert')]"
      @update:model-value="(val) => $emit('update', val)">
    </q-input>

    <!-- NUMBER -->
    <q-input
      v-if="field_data.type == 'number'"
      type="number"
      filled
      stack-label
      autogrow
      :disable="disable"
      :dense="dense"
      :label="field_data.label"
      :hint="field_data.hint"
      :model-value="field_data.value"
      lazy-rules
      :rules="[value => (field_data.required ? !!value : true) || $t('field_required_alert')]"
      @update:model-value="val => $emit('update', parseFloat(val))">
    </q-input>

    <!-- BOOLEAN -->
    <q-checkbox
      v-if="field_data.type == 'boolean'"
      :disable="disable"
      :dense="dense"
      :label="field_data.label"
      :model-value="field_data.value ?? false"
      :rules="[value => (field_data.required ? !!value : true) || $t('field_required_alert')]"
      @update:model-value="val => $emit('update', val)">
    </q-checkbox>

    <!-- CHOICE -->
    <!-- DATE -->
    <!-- TIME -->
  </div>
</template>

<script>
export default {

  name: 'FormField',

  props: {
    field_data: {
      type: Object,
      required: true
    },
    dense: {
      type: Boolean,
      default: false
    },
    disable: {
      type: Boolean,
      default: false
    }
  },
}
</script>

<style lang="css" scoped>
</style>

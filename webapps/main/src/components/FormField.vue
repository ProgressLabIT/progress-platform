<template>
  <div>
    <!-- TEXT -->
    <q-input
      v-if="field_meta.type == 'text'"
      filled
      stack-label
      autogrow
      lazy-rules
      :label="field_meta.label"
      :hint="field_meta.hint"
      :model-value="value"
      :rules="[value => (field_meta.required ? !!value : true) || $t('field_required_alert')]"
      @update:model-value="(val) => $emit('update', val)">
    </q-input>

    <!-- NUMBER -->
    <q-input
      v-if="field_meta.type == 'number'"
      type="number"
      filled
      stack-label
      autogrow
      :label="field_meta.label"
      :hint="field_meta.hint"
      :model-value="value"
      lazy-rules
      :rules="[value => (field_meta.required ? !!value : true) || $t('field_required_alert')]"
      @update:model-value="val => $emit('update', parseFloat(val))">
    </q-input>

    <!-- BOOLEAN -->
    <q-checkbox
      v-if="field_meta.type == 'boolean'"
      :label="field_meta.label"
      :model-value="value"
      :rules="[value => (field_meta.required ? !!value : true) || $t('field_required_alert')]"
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
    field_meta: {
      type: Object,
      required: true
    },
    value: null
  },
}
</script>

<style lang="css" scoped>
</style>

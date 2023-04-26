<template>
  <div>
    <!-- TEXT -->
    <q-input
      v-if="field_data.type == 'text'"
      filled
      stack-label
      autogrow
      lazy-rules
      input-debounce="100"
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
      input-debounce="100"
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
    <q-select
      v-if="field_data.type == 'choice'"
      filled
      stack-label
      use-input
      clearable
      :disable="disable"
      :dense="dense"
      :label="field_data.label"
      :options="options"
      option-label="value"
      @filter="filter"
      :model-value="field_data.value"
      @update:model-value="val => $emit('update', val)">
    </q-select>
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

  data() {
    return {
      origin_list: [],
      options: []
    }
  },

  methods: {
    initOptions() {
      this.$api.get('list', { params: { field_key: this.field_data._key }})
      .then( resp => {
        this.origin_list = resp.data
        this.options = resp.data
      })
    },

    filter(value, update) {
      if (value === '') {
        update(() => {
          this.initOptions()
        })
        return
      }
      update(() => {
        const needle = value.toLowerCase()
        this.options = this.origin_list.filter(option => {
          return option.value.toLowerCase().includes(needle)
        })
      })
    }
  },

  created() {
    if (this.field_data.type == 'choice') {
      this.initOptions()
    }
  }
}
</script>

<style lang="css" scoped>
</style>

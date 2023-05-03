<template>
  <div>

    <!-- TEXT -->
    <div v-if="field_data.type == 'text'" class="q-mb-lg">
      <q-input
        filled
        stack-label
        autogrow
        lazy-rules
        input-debounce="100"
        hide-bottom-space
        :disable="disable"
        :dense="dense"
        :label="field_data.label"
        :model-value="field_data.value"
        :rules="[value => (field_data.required ? !!value : true) || $t('field_required_alert')]"
        @update:model-value="(val) => $emit('update', val)">
      </q-input>
      <div class="smaller q-px-sm q-mt-xs">
        {{ field_data.hint }}
      </div>
    </div>

    <!-- NUMBER -->
    <div v-if="field_data.type == 'number'" class="q-mb-lg">
      <q-input
        type="number"
        filled
        stack-label
        hide-bottom-space
        input-debounce="100"
        :disable="disable"
        :dense="dense"
        :label="field_data.label"
        :model-value="field_data.value"
        lazy-rules
        :rules="[value => (field_data.required ? !!value : true) || $t('field_required_alert')]"
        @update:model-value="val => $emit('update', parseFloat(val))">
      </q-input>
      <div class="smaller q-px-sm q-mt-xs">
        {{ field_data.hint }}
      </div>
    </div>

    <!-- BOOLEAN -->
    <div v-if="field_data.type == 'boolean'" class="q-mb-lg">
      <q-checkbox
        :disable="disable"
        :dense="dense"
        :label="field_data.label"
        :model-value="field_data.value ?? false"
        :rules="[value => (field_data.required ? !!value : true) || $t('field_required_alert')]"
        @update:model-value="val => $emit('update', val)">
      </q-checkbox>
      <div class="smaller q-px-sm q-mt-xs">
        {{ field_data.hint }}
      </div>
    </div>

    <!-- CHOICE -->
    <div v-if="field_data.type == 'choice'" class="q-mb-lg">
      <q-select
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
      <div class="smaller q-px-sm q-mt-xs">
        {{ field_data.hint }}
      </div>
    </div>

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

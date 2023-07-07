<template>
  <div class="q-mb-lg">

    <!-- TEXT -->
    <q-input
      v-if="field_data.type == 'text'"
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

    <!-- NUMBER -->
    <q-input
      v-if="field_data.type == 'number'"
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
      @update:model-value="val => $emit('update', val)"
      input-class="cursor-pointer">
    </q-select>

    <!-- DATE -->
    <q-input
      v-if="field_data.type == 'date'"
      filled
      stack-label
      :label="field_data.label"
      v-model="field_data.value"
      :placeholder="$t('date_format')"
      input-class="cursor-pointer">
      <template v-slot:append>
        <q-icon name="mdi-calendar" />
      </template>
      <q-popup-proxy anchor="center middle" self="center middle" @hide="blur">
        <q-date minimal v-model="field_data.value">
          <div class="row items-center justify-end">
            <q-btn v-close-popup :label="$t('close')" color="primary" flat />
          </div>
        </q-date>
      </q-popup-proxy>
    </q-input>

    <!-- TIME -->
    <q-input
      v-if="field_data.type == 'time'"
      stack-label
      filled
      :label="field_data.label"
      v-model="field_data.value"
      inpu-class="cursor-pointer"
      placeholder="HH:mm">
      <template v-slot:append>
        <q-icon name="mdi-clock-outline" />
      </template>
      <q-popup-proxy anchor="center middle" self="center middle" @hide="blur">
        <q-time v-model="field_data.value" format24h>
          <div class="row items-center justify-end">
            <q-btn v-close-popup :label="$t('close')" color="primary" flat />
          </div>
        </q-time>
      </q-popup-proxy>
    </q-input>

    <!-- ATTACHMENT -->
    <q-file
      v-if="field_data.type == 'attachment'"
      multiple
      append
      use-chips
      counter
      clearable
      filled
      stack-label
      v-model="field_data.value"
      :label="field_data.label">
      <template #append>
        <q-icon name="mdi-paperclip" />
      </template>
    </q-file>

    <!-- HINT -->
    <div class="smaller q-px-sm q-mt-xs">
      {{ field_data.hint }}
    </div>
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
    },

    blur() {
      document.activeElement.blur()
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

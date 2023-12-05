<template>
  <div class="q-mb-lg">

    <!-- TEXT -->
    <q-input
      v-if="field_type == 'text'"
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
      v-if="field_type == 'number'"
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
      v-if="field_type == 'boolean'"
      :disable="disable"
      :dense="dense"
      :label="field_data.label"
      :model-value="field_data.value ?? false"
      :rules="[value => (field_data.required ? !!value : true) || $t('field_required_alert')]"
      @update:model-value="val => $emit('update', val)">
    </q-checkbox>

    <!-- TERNARY -->
    <!-- TODO: Implement required behavior (?) -->
    <div v-if="field_type === 'ternary'" class="row items-center">
      <div class="col-1 items-center">
        <q-avatar
          :color="field_data.value !== undefined ? 'theme-green' : 'transparent'"
          size="24px"
          class="row flex-center text-center text-body2 font-weight-medium"
        >
          <q-icon v-if="field_data.value === undefined" size="sm" name="mdi-progress-question" />
          <q-icon v-else class="solid-white" name="mdi-check" />
        </q-avatar>
      </div>

      <div class="col-6 items-center">
        <p class="text-body1 q-ma-none">{{ field_data.label }}</p>
      </div>

      <q-space />

      <div class="col-auto">
        <q-btn
          size="lg"
          unelevated
          :flat="field_data.value !== false"
          :disable="disable"
          :dense="dense"
          color="theme-red"
          style="width: 100px"
          @click="$emit('update', field_data.value === false ? undefined : false)"
        >
          <span class="text-h4 display weight-bold">{{ $t('no') }}</span>
        </q-btn>

        <q-btn
          size="lg"
          unelevated
          :flat="field_data.value !== true"
          :disable="disable"
          :dense="dense"
          color="theme-green"
          style="width: 100px"
          class="q-ml-lg"
          @click="$emit('update', field_data.value === true ? undefined : true)"
        >
          <span class="text-h4 display weight-bold">{{ $t('yes') }}</span>
        </q-btn>
      </div>
    </div>

    <!-- CHOICE -->
    <q-select
      v-if="field_type == 'choice'"
      filled
      stack-label
      use-input
      clearable
      :disable="disable"
      :dense="dense"
      :label="field_data.label"
      :options="options"
      :debounce="300"
      :loading="loading"
      option-label="value"
      @filter="filter"
      :model-value="field_data.value"
      @update:model-value="val => $emit('update', val)"
      input-class="cursor-pointer">
    </q-select>

    <!-- DATE -->
    <!-- FIXME: Do not mutate the prop, emit 'update' event like other types instead -->
    <q-input
      v-if="field_type == 'date'"
      filled
      stack-label
      :disable="disable"
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
    <!-- FIXME: Do not mutate the prop, emit 'update' event like other types instead -->
    <q-input
      v-if="field_type == 'time'"
      stack-label
      filled
      :label="field_data.label"
      :disable="disable"
      v-model="field_data.value"
      input-class="cursor-pointer"
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

    <!-- FILES -->
    <!-- <q-file
      v-if="field_type == 'files'"
      multiple
      append
      :use-chips="!disable"
      counter
      clearable
      filled
      stack-label
      :disable="disable"
      v-model="field_data.value"
      :label="field_data.label">
      <template #append>
        <q-icon name="mdi-folder-open-outline" />
      </template>
    </q-file> -->
    <div v-if="field_type == 'files'">
      <FilesList
        :label="field_data.label"
        :disable="disable"
        :files="field_data.value"
        :root_path="`${root_path}/${field_data._key}`"
        @addFiles="addFiles"
        @deleteFile="deleteFile"
        @restoreFile="restoreFile">
      </FilesList>
    </div>


    <!-- HINT -->
    <div class="smaller q-px-sm q-mt-xs">
      {{ field_data.hint }}
    </div>
  </div>
</template>

<script>
import FilesList from '@/components/FilesList.vue'

export default {
  name: 'FormField',

  components: {
    FilesList
  },

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
    },
    root_path: {
      type: String,
    }
  },

  data() {
    return {
      options: [],
      loading: false
    }
  },

  computed: {
    field_type() {
      return this.$store.getters.getCustomFieldByKey(this.field_data._key)?.type
    }
  },

  methods: {
    initOptions() {
      this.$api.get('list', { params: { field_key: this.field_data._key }})
      .then(resp => this.options = resp.data)
    },

    filter(value, update) {
      this.loading = true
      if (value === '') {
        update(() => {
          this.initOptions()
          this.loading = false
        })
        return
      }
      update(() => {
        const needle = value.toLowerCase()
        this.$api.get('list', {
          params: {
            field_key: this.field_data._key,
            search: value
          }
        })
        .then(resp =>{
          this.options = resp.data
        })
        this.loading = false
      })
    },

    addFiles(file_list) {
      let working_list = this.field_data.value ?? []
      const files = Array.from(file_list)
      // Don't add files already in the list
      files.forEach( (new_file, index) => {
        const already_in_list = working_list.some( existing_file => existing_file.name == new_file.name )
        if (already_in_list) {
          const replace = window.confirm(
            this.$capitalize(this.$t('product.alerts.doc_name_exists',1, {filename: new_file.name}))
          )
          if (replace) {
            working_list.splice(index, 1)
          }
          else {
            return
          }
        }
        working_list.push({
          content: new_file,
          name: new_file.name,
          temp: true,
          delete: false,
          path: window.URL.createObjectURL(new_file),
          size: new_file.size
        })
      })
      this.field_data.value = working_list
    },

    deleteFile(index) {
      const file = this.field_data.value[index]
      file.temp ? this.field_data.value.splice(index, 1) : file.delete = true
    },

    restoreFile(index) {
      this.field_data.value[index].delete = false
    },

    blur() {
      document.activeElement.blur()
    }
  },

  created() {
    if (this.field_type == 'choice') {
      this.initOptions()
    }
  }
}
</script>

<style lang="css" scoped>
</style>

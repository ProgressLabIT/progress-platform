<template>
  <LoadingSignal v-if="!data_ready" />

  <div v-else class="row full-height">
    <div class="full-height column col-3">

      <q-input
        dense
        filled
        class="q-px-md q-pt-md"
        :placeholder="$capitalize($t('search'))"
        v-model="search_text">
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>

      <div class="row q-mt-md q-px-lg q-py-sm text-h6 text-uppercase weight-bold">
        <div class="col-3">
          {{ $t('type') }}
        </div>
        <div class="col">
          {{ $t('name') }}
        </div>
      </div>

      <q-separator />

      <!-- ISSUE TYPE LIST -->
      <div class="scroll col">
        <div
          v-for="(field, index) in filtered_fields"
          class="row pointer q-px-lg q-py-xs medium full-width"
          :class="{ 'alternate-row': index % 2 == 0, 'bg-blue-backdrop': field._key == selected_field_key }"
          :key="field._key"
          style="white-space: nowrap;"
          @click="showFieldDetail(field._key)">
          <div class="col-3">
            <q-icon :name="getFieldIcon(field.type)" />
          </div>
          <div class="col">
            {{ $capitalize(field.name) }}
          </div>
        </div>
      </div>

      <q-separator />

      <!-- ISSUE TYPE LIST COUNT -->
      <div class="row flex-center smaller q-py-xs">
        {{ filtered_fields.length }} {{ $t('of') }} {{ field_list.length }}
      </div>

      <div class="q-pa-md q-mt-auto">
        <q-btn
          class="full-width q-mt-auto"
          color="theme-blue"
          :label="$t('new')"
          @click="show_designer = true">
        </q-btn>
      </div>
    </div>

    <BaseDialog
      :show="show_designer"
      :no-backdrop-dismiss="false">
      <FormFieldNew
        @close="show_designer = false"
        @created="getFields">
      </FormFieldNew>
    </BaseDialog>

    <q-separator vertical />

    <!-- FIELD DATA -->
    <div class="col full-height" v-if="data_ready">
      <router-view
        :template="selected_template"
        @reload="getTemplates">
      </router-view>
    </div>
  </div>
</template>

<script>
import BaseModalScreen from '@/components/BaseModalScreen.vue'

export default {
  name: 'PrintTemplateLibrary',

  components: {
    BaseModalScreen
  },

  data () {
    return {
      data_ready: false,
      search_text: null,
      template_list: [],
      show_designer: false
    }
  },

  computed: {
    filtered_templates() {
      return this.template_list.filter(t => t.toLowerCase().includes(this.search_text.toLowerCase()))
    }
  },

  methods: {
    getTemplates() {
      this.$api.get('print-template').then( resp => {
        this.template_list = resp.data.sort()
        this.data_ready = true
      })
    }
  },

  created() {
    this.getTemplates()
  }
}

</script>

<template>
  <div class="fit">
    <LoadingSignal v-if="!data_ready" />

    <div v-else class="row q-col-gutter-md q-ml-none q-mt-none">
      <div class="col-2"
        v-for="template in template_list"
        :key="template._key">
        <q-card
          square
          bordered
          class="surface2">
          <q-card-section class="text-h3 row items-end">
            <q-icon
              class=""
              name="mdi-file-document"
              size="sm">
            </q-icon>
            <div class="q-ml-sm">
              {{ template.name }}
            </div>
          </q-card-section>
          <q-card-section>
            {{ template.description }}
          </q-card-section>
          <q-card-section class="row justify-end">
            <q-btn
              size="sm"
              @click="editTemplate(template._key)"
              :label="$t('edit')"
              color="theme-blue">
            </q-btn>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <q-btn
      round
      class="absolute-bottom-right q-mb-lg q-mr-lg"
      color="theme-blue"
      icon="mdi-plus"
      @click="openNewTemplate">
    </q-btn>

    <PrintTemplateDesigner
      :show="show_designer"
      :edit_template="edit_template"
      @close="resetDesigner"
      @saved="getTemplates()">
    </PrintTemplateDesigner>

  </div>
</template>

<script>
import LoadingSignal from '@/components/LoadingSignal.vue'
import PrintTemplateDesigner from '@/components/PrintTemplateDesigner.vue'

export default {
  name: 'PrintTemplateLibrary',

  components: {
    LoadingSignal,
    PrintTemplateDesigner
  },

  data () {
    return {
      data_ready: false,
      search_text: null,
      template_list: [],
      show_designer: false,
      edit_template: null
    }
  },

  methods: {
    getTemplates() {
      this.$api.get('print-template').then( resp => {
        this.template_list = resp.data.sort()
        this.data_ready = true
      })
    },

    editTemplate(template_key) {
      this.$api.get('print-template', { params: { template_key }}).then(resp =>{
        this.edit_template = resp.data
        this.show_designer = true
      })
    },

    openNewTemplate() {
      this.show_designer = true
    },

    resetDesigner() {
      this.show_designer = false
      this.edit_template = null
    }
  },

  created() {
    this.getTemplates()
  }
}

</script>
<style lang="sass">

</style>

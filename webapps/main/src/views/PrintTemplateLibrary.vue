<template>
  <div>
    <LoadingSignal v-if="!data_ready" />

    <q-list class="q-pr-xl scroll">
      <q-item v-for="template in template_list" :key="template._key">
        <q-item-section top class="q-pa-md col-5 q-pr-xl">
          <q-item-label class="text-h4 highlight">
            {{ template.name }}
          </q-item-label>
        </q-item-section>
        <q-item-section class="col-auto">
          <q-btn
            @click="editTemplate(template._key)"
            :label="$t('edit')"
            color="theme-blue">
          </q-btn>
        </q-item-section>
      </q-item>
    </q-list>

    <q-btn
      class="full-width q-mt-auto"
      color="theme-blue"
      :label="$t('new')"
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

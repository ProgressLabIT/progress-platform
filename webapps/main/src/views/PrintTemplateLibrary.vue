<template>
  <div class="fit scroll q-pa-md">
    <LoadingSignal v-if="!data_ready" />

    <div v-else class="row q-col-gutter-md">
      <div
        class="col-3"
        v-for="template in template_list"
        :key="template._key">
        <PrintTemplateCard
          :template="template"
          :allow_edit="true"
          @saved="getTemplates">
        </PrintTemplateCard>
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
      @close="resetDesigner"
      @saved="getTemplates()">
    </PrintTemplateDesigner>

  </div>
</template>

<script>
import LoadingSignal from '@/components/LoadingSignal.vue'
import PrintTemplateCard from '@/components/PrintTemplateCard.vue'
import PrintTemplateDesigner from '@/components/PrintTemplateDesigner.vue'

export default {
  name: 'PrintTemplateLibrary',

  components: {
    LoadingSignal,
    PrintTemplateCard,
    PrintTemplateDesigner
  },

  data () {
    return {
      data_ready: false,
      search_text: null,
      template_list: [],
      show_designer: false,
    }
  },

  methods: {
    getTemplates() {
      this.$api.get('print-template').then( resp => {
        this.template_list = resp.data.sort()
        this.data_ready = true
      })
    },

    openNewTemplate() {
      this.show_designer = true
    },

    resetDesigner() {
      this.show_designer = false
    }
  },

  created() {
    this.getTemplates()
  }
}

</script>
<style lang="sass">

</style>

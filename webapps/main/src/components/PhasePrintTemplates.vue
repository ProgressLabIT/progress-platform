<template>
  <div class="fit q-pa-lg column scroll">

    <div
      v-if="phase.print_templates.length"
      class="row q-col-gutter-md q-ma-none col-auto">
      <div class="col-3"
        v-for="template in phase.print_templates.filter(t => !('trash' in t))"
        :key="template._key">
        <PrintTemplateCard :template="template" />
      </div>
    </div>

    <div v-else>
      <NoDataAlert />
    </div>

    <q-space></q-space>

    <BaseAutocompleteTemplate
      v-if="edit_mode"
      class="q-px-sm q-mt-md"
      :label="$t('print_template_add')"
      @select="addTemplate"
      :selected="phase.print_templates">
    </BaseAutocompleteTemplate>

  </div>
</template>

<script>
import LoadingSignal from '@/components/LoadingSignal.vue'
import NoDataAlert from '@/components/NoDataAlert.vue'
import PrintTemplateCard from '@/components/PrintTemplateCard.vue'
import BaseAutocompleteTemplate from '@/components/BaseAutocompleteTemplate.vue'

export default {
  name: 'PrintTemplateLibrary',

  components: {
    BaseAutocompleteTemplate,
    LoadingSignal,
    NoDataAlert,
    PrintTemplateCard
  },

  props: {
    phase: {
      type: Object,
      required: true
    },

    product_data: {
      type: Object,
      required: true
    },

    edit_mode: {
      type: Boolean
    }
  },

  data () {
    return {
      template_list: [],
    }
  },

  computed: {
    current_phase_index() {
      return this.product_data.last_phase
    }
  },

  methods: {

    addTemplate(selection) {
      this.$store.commit('ADD_TEMP_PHASE_TEMPLATE', {
        phase_index: this.current_phase_index,
        template: selection
      })
    },

    deleteTemplate(index) {
      this.$store.commit('DELETE_TEMP_PHASE_TEMPLATE', {
        phase_index: this.current_phase_index,
        template_index: index
      })
    }
  },
}

</script>
<style lang="sass">

</style>

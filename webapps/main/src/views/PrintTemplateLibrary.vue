<template>
  <div class="fit scroll q-pa-md">
    <LoadingSignal v-if="!data_ready" />

    <div v-else class="row q-col-gutter-md">
      <div v-for="template in template_list" :key="template._key" class="col-3">
        <PrintTemplateCard
          :template="template"
          allow-edit
          @saved="getTemplates"
        />
      </div>
    </div>

    <q-btn
      round
      class="absolute-bottom-right q-mb-lg q-mr-lg"
      color="theme-blue"
      icon="mdi-plus"
      @click="openNewTemplate"
    />

    <PrintTemplateDesigner
      :show="show_designer"
      @close="resetDesigner"
      @saved="getTemplates"
    />
  </div>
</template>

<script>
import LoadingSignal from '@/components/LoadingSignal.vue';
import PrintTemplateCard from '@/components/PrintTemplateCard.vue';
import PrintTemplateDesigner from '@/components/PrintTemplateDesigner.vue';

export default {
  name: 'PrintTemplateLibrary',

  components: {
    LoadingSignal,
    PrintTemplateCard,
    PrintTemplateDesigner,
  },

  data() {
    return {
      data_ready: false,
      search_text: null,
      template_list: [],
      show_designer: false,
    };
  },

  created() {
    this.getTemplates();
  },

  methods: {
    async getTemplates() {
      const { data } = await this.$api.get('print-template');
      this.template_list = data.sort();
      this.data_ready = true;
    },

    openNewTemplate() {
      this.show_designer = true;
    },

    resetDesigner() {
      this.show_designer = false;
    },
  },
};
</script>

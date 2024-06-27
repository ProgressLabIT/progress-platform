<template>
  <div class="fit scroll q-pa-md">
    <LoadingSignal v-if="isLoading" />
    <div v-else class="row q-col-gutter-md">
      <div v-for="template in templates" :key="template._key" class="col-3">
        <PrintTemplateCard
          :template="template"
          allow-edit
          allow-delete
          @saved="getTemplates"
          @delete="getTemplates"
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
      :show="showDesigner"
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

  props: {
    context: {
      type: String,
      default: undefined,
      validator: (value) =>
        ['product', 'phase', 'step', 'issue_type'].includes(value),
    },

    contextKey: {
      type: String,
      default: undefined,
    },
  },

  data() {
    return {
      isLoading: true,
      templates: [],
      showDesigner: false,
    };
  },

  created() {
    this.getTemplates();
  },

  methods: {
    async getTemplates() {
      this.isLoading = true;
      const { data } = await this.$api.get('print-template', {
        params: {
          context: this.context,
          context_key: this.contextKey,
        },
      });
      this.templates = data.sort();
      this.isLoading = false;
    },

    openNewTemplate() {
      this.showDesigner = true;
    },

    resetDesigner() {
      this.showDesigner = false;
    },
  },
};
</script>

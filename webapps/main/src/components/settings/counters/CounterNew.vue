<template>
  <BaseActionFormCard
    :title="$t('counter_add')"
    @submit="addCounter"
    @cancel="$emit('close')"
  >
    <q-input
      v-model="new_counter.name"
      :rules="[(value) => !!value || $t('field_required_alert')]"
      hide-bottom-space
      autogrow
      :label="$t('name')"
      filled
      class="q-mt-md"
    />

    <TemplateSelect v-model="template_model" />

    <!--<q-input
      v-model="new_counter.frequency"
      autogrow
      :rules="[(value) => !!value || $t('field_required_alert')]"
      :label="$t('frequency')"
      filled
      class="q-mt-md"
    />-->

    <q-select
      v-model="new_counter.frequency"
      filled
      :rules="[(value) => !!value || $t('field_required_alert')]"
      :options="[$t('year'), $t('month'), $t('week'), $t('day')]"
      :label="$t('frequency')"
      class="q-mt-md"
      @update:model-value="(selection) => refreshResetDate(selection)"
    />

    <q-input
      v-model="new_counter.reset_date"
      filled
      readonly
      disable
      mask="date"
      :label="$t('reset_date')"
      class="q-mt-md"
    >
      <template #append>
        <q-icon name="mdi-calendar" class="cursor-pointer">
          <q-popup-proxy cover transition-show="scale" transition-hide="scale">
            <q-date v-model="new_counter.reset_date">
              <div class="row items-center justify-end">
                <q-btn v-close-popup label="Close" color="primary" flat />
              </div>
            </q-date>
          </q-popup-proxy>
        </q-icon>
      </template>
    </q-input>
  </BaseActionFormCard>
</template>

<script>
import { date } from 'quasar';
import { ref } from 'vue';
import BaseActionFormCard from '@/components/BaseActionFormCard.vue';
import TemplateSelect from '@/components/settings/counters/TemplateSelect.vue';
import { calculateNextResetDate } from '@/lib/dateUtils';

export default {
  name: 'CounterNew',

  components: {
    BaseActionFormCard,
    TemplateSelect,
  },

  emits: ['close', 'created'],

  setup() {
    const template_model = ref(null);

    return {
      template_model,
    };
  },

  data() {
    return {
      new_counter: {
        name: null,
        frequency: null,
        template: [],
        reset_date: null,
      },
    };
  },

  methods: {
    refreshResetDate(reset_period) {
      this.new_counter.reset_date = calculateNextResetDate({
        reset_period: this.getFrequency(reset_period),
      }).resetDate;
    },

    getFrequency(reset_period) {
      switch (reset_period) {
        case this.$t('day'):
          return 'day';
        case this.$t('week'):
          return 'week';
        case this.$t('month'):
          return 'month';
        case this.$t('year'):
          return 'year';
        default:
          return undefined;
      }
    },

    addCounter() {
      const data = {
        name: this.new_counter.name,
        frequency: this.getFrequency(this.new_counter.frequency),
        template: this.template_model,
        reset_date: date.formatDate(
          this.new_counter.reset_date,
          'YYYY-MM-DDTHH:mm:ss.SSSZ',
        ),
      };
      this.$api.post('counter', data).then(() => {
        this.$emit('created');
        this.$emit('close');
      });
    },
  },
};
</script>

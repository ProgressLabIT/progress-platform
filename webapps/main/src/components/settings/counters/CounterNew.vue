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

    <TemplateSelect
      v-model="template_model"
      :error="!template_check.valid"
      :error-message="
        !template_check.valid ? $t(template_check.reason) : ''
      "
    />

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
      :options="[$t('none'), $t('year'), $t('month'), $t('week'), $t('day')]"
      :label="$t('reset_frequency')"
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

    <div class="row q-mt-lg items-center">
      <div class="col-auto text-grey-7 q-mr-md">
        {{ $t('counter_preview') }}:
      </div>
      <div class="col">
        <code class="text-h6">{{ preview || '—' }}</code>
      </div>
    </div>

    <template #actions="{ uniqueFormId }">
      <q-btn
        type="submit"
        :form="uniqueFormId"
        color="theme-blue"
        :label="$t('save')"
        :disable="!template_check.valid"
      />
      <q-btn
        color="theme-grey"
        :label="$t('cancel')"
        @click="$emit('close')"
      />
    </template>
  </BaseActionFormCard>
</template>

<script>
import { date } from 'quasar';
import { ref } from 'vue';
import BaseActionFormCard from '@/components/BaseActionFormCard.vue';
import TemplateSelect from '@/components/settings/counters/TemplateSelect.vue';
import {
  renderCounterTemplate,
  validateCounterTemplate,
} from '@/lib/counterValidation';
import { calculateNextResetDate } from '@/lib/dateUtils';

export default {
  name: 'CounterNew',

  components: {
    BaseActionFormCard,
    TemplateSelect,
  },

  emits: ['close', 'created'],

  setup() {
    const template_model = ref([]);

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

  computed: {
    template_check() {
      return validateCounterTemplate(
        this.template_model,
        this.getFrequency(this.new_counter.frequency),
      );
    },

    preview() {
      return renderCounterTemplate(this.template_model, 1);
    },
  },

  methods: {
    refreshResetDate(reset_period) {
      this.new_counter.reset_date = calculateNextResetDate({
        reset_period: this.getFrequency(reset_period),
      }).resetDate;
    },

    getFrequency(reset_period) {
      switch (reset_period) {
        case this.$t('none'):
          return 'none';
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
      const frequency = this.getFrequency(this.new_counter.frequency);
      const check = validateCounterTemplate(this.template_model, frequency);
      if (!check.valid) {
        this.$q.notify({
          message: this.$t(check.reason),
          color: 'theme-red',
          timeout: 2500,
          position: 'top',
        });
        return;
      }
      const data = {
        name: this.new_counter.name,
        frequency,
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

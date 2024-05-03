<template>
  <BaseActionFormCard
    :title="$t('counter_new')"
    @submit="addCounter"
    @cancel="$emit('close')"
  >
    <q-input
      v-model="new_counter.name"
      :rules="[(value) => !!value || $t('counter_required_alert')]"
      hide-bottom-space
      autogrow
      :label="$t('name')"
      filled
      class="q-mt-md"
    />

    <q-select
      v-model="template_model"
      filled
      :label="$t('template')"
      use-input
      use-chips
      multiple
      input-debounce="0"
      :options="filterOptions"
      class="q-mt-md"
      @new-value="createValue"
      @filter="filterFn"
    />

    <q-input
      v-model="new_counter.frequency"
      autogrow
      :label="$t('frequency')"
      filled
      class="q-mt-md"
    />

    <q-input
      v-model="new_counter.reset_date"
      filled
      mask="date"
      :label="$t('reset_date')"
      :rules="['date']"
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

const templateOptions = ['%y', '%m', '%d', '/', '#2', '#3', '#4', '#5', '#6'];

export default {
  name: 'CounterNew',

  components: {
    BaseActionFormCard,
  },

  emits: ['close', 'created'],

  setup() {
    const template_model = ref(null);
    const filterOptions = ref(templateOptions);

    return {
      template_model,
      filterOptions,

      createValue(val, done) {
        // Calling done(var) when new-value-mode is not set or is "add", or done(var, "add") adds "var" content to the model
        // and it resets the input textbox to empty string
        // ----
        // Calling done(var) when new-value-mode is "add-unique", or done(var, "add-unique") adds "var" content to the model
        // only if is not already set and it resets the input textbox to empty string
        // ----
        // Calling done(var) when new-value-mode is "toggle", or done(var, "toggle") toggles the model with "var" content
        // (adds to model if not already in the model, removes from model if already has it)
        // and it resets the input textbox to empty string
        // ----
        // If "var" content is undefined/null, then it doesn't tampers with the model
        // and only resets the input textbox to empty string

        if (val.length > 0) {
          const modelValue = (template_model.value || []).slice();

          val
            .split(/[,;|]+/)
            .map((v) => v.trim())
            .filter((v) => v.length > 0)
            .forEach((v) => {
              if (templateOptions.includes(v) === false) {
                templateOptions.push(v);
              }
              if (modelValue.includes(v) === false) {
                modelValue.push(v);
              }
            });

          done(null);
          template_model.value = modelValue;
        }
      },

      filterFn(val, update) {
        update(() => {
          if (val === '') {
            filterOptions.value = templateOptions;
          } else {
            const needle = val.toLowerCase();
            filterOptions.value = templateOptions.filter(
              (v) => v.toLowerCase().indexOf(needle) > -1,
            );
          }
        });
      },
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
    addCounter() {
      const data = {
        name: this.new_counter.name,
        frequency: this.new_counter.frequency,
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

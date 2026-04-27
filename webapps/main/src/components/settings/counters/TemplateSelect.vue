<template>
  <q-select
    v-model="model"
    filled
    :label="$t('template')"
    use-input
    use-chips
    multiple
    input-debounce="0"
    :options="filterOptions"
    :error="error"
    :error-message="errorMessage"
    hide-bottom-space
    @new-value="createValue"
    @filter="filterFn"
  >
    <template #option="scope">
      <q-item v-bind="scope.itemProps">
        <q-item-section side>
          <code>{{ scope.opt }}</code>
        </q-item-section>
        <q-item-section caption>{{ describe(scope.opt) }}</q-item-section>
        <q-item-section side>
          <code class="text-grey-7">{{ sample(scope.opt) }}</code>
        </q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';

defineProps({
  error: { type: Boolean, default: false },
  errorMessage: { type: String, default: '' },
});

const { t } = useI18n();

const templateOptions = ['%y', '%Y', '%G', '%m', '%V', '%W', '%d', '%j', '%H', '%M', '#2', '#3', '#4', '#5', '#6'];

const TOKEN_DESCRIPTIONS = {
  '%y': 'counter_help_token_y',
  '%Y': 'counter_help_token_yyyy',
  '%G': 'counter_help_token_g',
  '%m': 'counter_help_token_m',
  '%V': 'counter_help_token_v',
  '%W': 'counter_help_token_w',
  '%d': 'counter_help_token_d',
  '%j': 'counter_help_token_j',
  '%H': 'counter_help_token_h',
  '%M': 'counter_help_token_min',
};

const TOKEN_SAMPLES = {
  '%y': '26',
  '%Y': '2026',
  '%G': '2026',
  '%m': '04',
  '%V': '17',
  '%W': '17',
  '%d': '27',
  '%j': '117',
  '%H': '15',
  '%M': '42',
};

function describe(opt) {
  if (TOKEN_DESCRIPTIONS[opt]) return t(TOKEN_DESCRIPTIONS[opt]);
  if (/^#\d+$/.test(opt)) return t('counter_help_token_tick');
  return t('counter_help_token_literal');
}

function sample(opt) {
  if (TOKEN_SAMPLES[opt]) return TOKEN_SAMPLES[opt];
  const tick = /^#(\d+)$/.exec(opt);
  if (tick) return '13'.padStart(parseInt(tick[1], 10), '0');
  return opt;
}

const model = defineModel({ default: () => [] });
const filterOptions = ref(templateOptions);

function createValue(val, done) {
  if (val.length > 0) {
    const modelValue = (model.value || []).slice();

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

    model.value = modelValue;
    done(val);
  }
}

function filterFn(val, update) {
  update(() => {
    if (val === '') {
      filterOptions.value = templateOptions;
    } else {
      filterOptions.value = templateOptions.filter((v) => v.indexOf(val) > -1);
    }
  });
}
</script>

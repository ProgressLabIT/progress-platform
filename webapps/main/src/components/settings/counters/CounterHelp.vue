<template>
  <div class="q-py-sm text-body2">
    <p class="q-mb-sm">{{ $t('counter_help_intro') }}</p>
    <p class="q-mb-sm">{{ $t('counter_help_reset') }}</p>

    <q-expansion-item
      icon="mdi-information-outline"
      :label="$t('counter_help_legend_title')"
      header-class="text-theme-blue q-px-none"
      dense
    >
      <q-markup-table dense flat bordered class="bg-transparent q-mt-xs">
        <tbody>
          <tr v-for="row in legend" :key="row.token">
            <td class="weight-bold">
              <code>{{ row.token }}</code>
            </td>
            <td>{{ $t(row.label) }}</td>
            <td class="text-grey-7">{{ row.example }}</td>
          </tr>
        </tbody>
      </q-markup-table>

      <div class="q-mt-sm">
        <span class="weight-bold">{{ $t('counter_help_example') }}:</span>
        <code class="q-ml-xs">['%y', '/', '#5']</code>
        <span class="q-ml-xs">→</span>
        <code class="q-ml-xs">{{ example_output }}</code>
      </div>
    </q-expansion-item>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const legend = [
  { token: '%Y', label: 'counter_help_token_yyyy', example: '2026' },
  { token: '%y', label: 'counter_help_token_y', example: '26' },
  { token: '%G', label: 'counter_help_token_g', example: '2026' },
  { token: '%m', label: 'counter_help_token_m', example: '04' },
  { token: '%V', label: 'counter_help_token_v', example: '17' },
  { token: '%W', label: 'counter_help_token_w', example: '17' },
  { token: '%d', label: 'counter_help_token_d', example: '27' },
  { token: '%j', label: 'counter_help_token_j', example: '117' },
  { token: '%H', label: 'counter_help_token_h', example: '15' },
  { token: '%M', label: 'counter_help_token_min', example: '42' },
  { token: '#N', label: 'counter_help_token_tick', example: '#5 → 00013' },
  { token: 'abc', label: 'counter_help_token_literal', example: '/' },
];

const example_output = computed(() => {
  const yy = String(new Date().getFullYear()).slice(-2);
  return `${yy}/00013`;
});
</script>

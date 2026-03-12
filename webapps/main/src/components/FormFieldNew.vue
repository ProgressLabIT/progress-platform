<template>
  <BaseActionFormCard
    :title="$t('field_new')"
    @submit="addField"
    @cancel="$emit('close')"
  >
    <q-select
      v-model="new_field.type"
      :options="field_types"
      emit-value
      map-options
      :label="$t('type')"
      filled
    >
      <template #option="scope">
        <q-item v-bind="scope.itemProps">
          <q-item-section avatar>
            <q-icon :name="scope.opt.icon" />
          </q-item-section>

          <q-item-section>
            <q-item-label>{{ scope.opt.label }}</q-item-label>
          </q-item-section>
        </q-item>
      </template>
    </q-select>

    <q-input
      v-model="new_field.name"
      :rules="[(value) => !!value || $t('field_required_alert')]"
      hide-bottom-space
      autogrow
      :label="$t('name')"
      filled
      class="q-mt-md"
    />

    <q-input
      v-model="new_field.label"
      autogrow
      :label="$t('label')"
      filled
      class="q-mt-md"
    />

    <q-input
      v-model="new_field.hint"
      autogrow
      :label="$t('hint')"
      filled
      class="q-mt-md"
    />
  </BaseActionFormCard>
</template>

<script>
import BaseActionFormCard from '@/components/BaseActionFormCard.vue';
import form from '@/mixins/form.js';

export default {
  name: 'FormFieldNew',

  components: {
    BaseActionFormCard,
  },

  mixins: [form],

  emits: ['close', 'created'],

  data() {
    return {
      new_field: {
        type: null,
        name: null,
        label: null,
        hint: null,
      },
    };
  },

  methods: {
    addField() {
      const data = {
        type: this.new_field.type,
        name: this.new_field.name,
        default_label: this.new_field.label,
        default_hint: this.new_field.hint,
      };
      this.$api.post('field', data)
        .then(() => {
          this.$store.dispatch('getCustomFields');
          this.$emit('created');
          this.$emit('close');
        })
        .catch((err) => {
          if (err?.response?.status === 409) {
            this.$q.notify({
              message: this.$t('field_slug_conflict'),
              color: 'negative',
              position: 'top',
              timeout: 4000,
            });
          }
        });
    },
  },
};
</script>

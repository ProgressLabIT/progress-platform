<template>
  <q-card square class="surface1" style="min-width: 400px">
    <q-card-section>
      <q-input
        v-model="search_text"
        :label="$capitalize($t('search'))"
        icon="mdi-magnify"
        debounce="300"
        dense
        square
        filled
        class="full-width"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>
    </q-card-section>

    <q-card-section>
      <q-virtual-scroll
        v-slot="{ item }"
        style="max-height: 200px"
        :items="filtered_fields"
        class="surface2"
      >
        <q-item clickable @click="$emit('select', item)">
          <q-item-section avatar>
            <q-icon :name="getFieldIcon(item.type)" />
          </q-item-section>
          <q-item-section>
            <q-item-label>
              <span class="highlight">
                {{ item.name }}
              </span>
              <span class="smaller q-ml-sm"> ({{ item.default_label }}) </span>
            </q-item-label>
            <q-item-label v-if="item.default_hint" caption>
              {{ item.default_hint }}
            </q-item-label>
          </q-item-section>
        </q-item>
      </q-virtual-scroll>
    </q-card-section>

    <q-card-section>
      <q-btn
        color="theme-blue"
        :label="$t('new')"
        icon="mdi-plus"
        class="full-width q-"
        @click="show_new_field = true"
      >
      </q-btn>
    </q-card-section>

    <BaseDialog :show="show_new_field" @close="show_new_field = false">
      <FormFieldNew
        @close="
          () => {
            show_new_field = false;
            fetchFields();
          }
        "
      />
    </BaseDialog>
  </q-card>
</template>

<script>
import BaseDialog from '@/components/BaseDialog.vue';
import FormFieldNew from '@/components/FormFieldNew.vue';
import multiMatch from '@/lib/MultiFieldSearch.js';
import form from '@/mixins/form.js';

export default {
  name: 'FormFieldSearch',

  components: {
    FormFieldNew,
    BaseDialog,
  },

  mixins: [form],

  props: {
    excludeKeys: {
      type: Array,
      default: () => [],
    },
  },

  emits: ['select'],

  data() {
    return {
      search_text: null,
      field_list: [],
      show_new_field: false,
      search_fields: ['name', 'default_label', 'default_hint'],
    };
  },

  computed: {
    filtered_fields() {
      return this.field_list
        .filter((f) => !this.excludeKeys.includes(f._key))
        .filter((f) => multiMatch(this.search_text, f, this.search_fields));
    },
  },

  created() {
    this.fetchFields();
  },

  methods: {
    fetchFields() {
      this.$api.get('field').then((resp) => {
        this.field_list = resp.data;
      });
    },
  },
};
</script>

<style lang="css" scoped></style>

<template>
  <q-select
    use-input
    filled
    :label="label"
    :stack-label="stackLabel"
    :dense="dense"
    :placeholder="placeholder_computed"
    :clearable="clearable"
    :options="options"
    :option-label="(operator) => operator.name + ' ' + operator.surname"
    :option-value="keyOnly ? '_key' : null"
    :model-value="value"
    input-debounce="200"
    :emit-value="keyOnly"
    :map-options="keyOnly"
    @filter="filter"
    @update:model-value="(selection) => $emit('select', selection)"
  >
    <template #option="scope">
      <q-item v-bind="scope.itemProps">
        <BaseUserAvatar :user="scope.opt" />
      </q-item>
    </template>

    <template #selected-item="scope">
      <BaseUserAvatar
        :user="scope.opt"
        :show-avatar="showAvatar"
        :dense="dense"
        reverse
      />
    </template>
  </q-select>
</template>

<script>
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import multiMatch from '@/lib/MultiFieldSearch.js';
export default {
  name: 'BaseAutocompletUser',

  components: {
    BaseUserAvatar,
  },

  props: {
    value: {
      type: [Object, String],
      default: null,
    },

    loadData: {
      type: Boolean,
      default: true,
    },

    label: {
      type: String,
      default: undefined,
    },

    keyOnly: {
      type: Boolean,
      default: false,
    },

    operatorOnly: {
      type: Boolean,
      default: true,
    },

    dense: {
      type: Boolean,
      default: false,
    },

    clearable: {
      type: Boolean,
      default: true,
    },

    placeholder: {
      type: String,
      default: '',
    },

    stackLabel: {
      type: Boolean,
      default: false,
    },

    showAvatar: {
      type: Boolean,
      default: true,
    },
  },

  emits: ['select'],

  data() {
    return {
      loading: false,
      options: [],
      search_fields: ['name', 'surname'],
    };
  },

  computed: {
    origin_list() {
      return this.operatorOnly
        ? this.$store.getters.operator_list()
        : this.$store.state.user.user_list;
    },

    placeholder_computed() {
      return this.value ? null : this.placeholder;
    },
  },

  created() {
    if (this.loadData) {
      this.loading = true;
      this.$store.dispatch('loadUsers').then(() => {
        this.initOptions();
        this.loading = false;
      });
    }
  },

  methods: {
    initOptions() {
      this.options = [...this.origin_list];
    },

    filter(value, update) {
      if (value === '') {
        update(() => {
          this.initOptions();
        });
        return;
      }
      update(() => {
        const needle = value.toLowerCase();
        this.options = this.origin_list.filter((option) => {
          return multiMatch(needle, option, this.search_fields);
        });
      });
    },
  },
};
</script>

<style lang="sass">
.q-select:has(.user-avatar) .q-field__input
  min-width: 0px !important
</style>

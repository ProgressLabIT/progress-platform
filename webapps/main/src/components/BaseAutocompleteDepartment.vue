<template>
  <q-select
    use-input
    dense
    :options="options"
    :option-label="(item) => $capitalize(item.name)"
    @filter="filterDepartments"
    :model-value="value"
    input-debounce="0"
    :option-value="key_only ? '_key' : false"
    :emit-value="key_only"
    :map-options="key_only"
    @update:model-value="(selection) => $emit('select', selection)"
  >
  </q-select>
</template>

<script>
export default {
  name: 'BaseAutocompleteDepartment',

  props: {
    value: {
      type: Object,
      deafult: null,
    },

    load_departments: {
      type: Boolean,
      default: true,
    },

    key_only: {
      type: Boolean,
      default: false,
    },
  },

  data() {
    return {
      loading: false,
      options: [],
    };
  },

  computed: {
    department_list() {
      return [
        ...this.$store.state.org.departments,
        {
          name: this.$t('unassigned', 1),
          _key: 'none',
          code: '-',
        },
      ];
    },
  },

  methods: {
    initOptions() {
      this.options = [...this.department_list];
    },

    filterDepartments(value, update) {
      if (value === '') {
        update(() => {
          this.initOptions();
        });
        return;
      }
      update(() => {
        const needle = value.toLowerCase();
        this.options = this.department_list.filter((d) => {
          const include = d.name.toLowerCase().includes(needle);
          return include;
        });
      });
    },
  },

  created() {
    if (this.load_departments) {
      this.loading = true;
      this.$store.dispatch('loadDepartments').then(() => {
        this.initOptions();
        this.loading = false;
      });
    }
  },
};
</script>

<style lang="css" scoped></style>

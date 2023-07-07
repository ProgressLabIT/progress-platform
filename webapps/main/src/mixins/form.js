export default {
  computed: {
    field_types() {
      return [
        { value: 'text', label: this.$t('field_type_text'), icon: 'mdi-alphabetical-variant' },
        { value: 'number', label: this.$t('field_type_number'), icon: 'mdi-numeric' },
        { value: 'boolean', label: this.$t('field_type_boolean'), icon: 'mdi-check-bold' },
        // { value: 'ternary', label: this.$t('field_type_ternary'), icon: '' }
        { value: 'choice', label: this.$t('field_type_choice'), icon: 'mdi-format-list-checks' },
        { value: 'date', label: this.$t('field_type_date'), icon: 'mdi-calendar' },
        { value: 'time', label: this.$t('field_type_time'), icon: 'mdi-clock-outline' },
      ]
    }
  },

  methods: {
    getFieldByType(type) {
      return this.field_types.find(f => f.value == type)
    },
    getFieldIcon(type) {
      return this.getFieldByType(type)?.icon
    },
    getFieldLabel(type) {
      return this.getFieldByType(type)?.label
    }
  }
}

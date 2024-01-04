import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

/**
 * @see {@link ../mixins/form.js}
 */
export function useFormFields() {
  const { t } = useI18n()

  const fields = computed(() => [
    { value: 'text', label: t('field_type_text'), icon: 'mdi-alphabetical-variant' },
    { value: 'number', label: t('field_type_number'), icon: 'mdi-numeric' },
    { value: 'boolean', label: t('field_type_boolean'), icon: 'mdi-check-bold' },
    { value: 'ternary', label: t('field_type_ternary'), icon: 'mdi-checkbox-intermediate-variant' },
    { value: 'choice', label: t('field_type_choice'), icon: 'mdi-format-list-checks' },
    { value: 'date', label: t('field_type_date'), icon: 'mdi-calendar' },
    { value: 'time', label: t('field_type_time'), icon: 'mdi-clock-outline' },
    { value: 'files', label: t('field_type_files'), icon: 'mdi-folder-outline' }
  ])
  const typeToIndexMap = fields.value.reduce((result, { value }, index) => {
    result[value] = index
    return result
  }, {})

  function getFieldByType(type) {
    return fields.value[typeToIndexMap[type]]
  }

  function getFieldIcon(type) {
    return getFieldByType(type)?.icon
  }

  function getFieldLabel(type) {
    return getFieldByType(type)?.label
  }

  return {
    fieldTypes: fields,
    getFieldByType,
    getFieldIcon,
    getFieldLabel
  }
}

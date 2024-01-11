<template>
  <q-select
    :model-value="modelValue"
    :emit-value="keyOnly"
    :map-options="keyOnly"
    :options="options"
    :option-value="keyOnly ? '_key' : null"
    option-label="name"
    use-input
    :input-debounce="100"
    filled
    behavior="menu"
    class="full-width"
    @filter="onFilter"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <template v-if="modelValue" #prepend>
      <q-icon
        :name="
          getFieldIcon(
            keyOnly
              ? options.find(({ _key }) => _key === modelValue)?.type
              : modelValue.type,
          )
        "
      />
    </template>

    <template #option="scope">
      <q-item v-bind="scope.itemProps" class="q-px-lg">
        <q-item-section avatar>
          <q-icon :name="getFieldIcon(scope.opt.type)" />
        </q-item-section>

        <q-item-section>
          <q-item-label class="text-body1 highlight">
            {{ $capitalize(scope.opt.name) }}
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useStore } from 'vuex';
import { useFormFields } from '@/composables/form';
import searchFields from '@/lib/MultiFieldSearch';

/**
 * @typedef {{
 *  _key: string;
 *  type: string;
 *  name: string;
 *  default_label: string;
 *  default_hint: string;
 * }} CustomField
 */

defineProps({
  modelValue: {
    type: [String, Object, null],
    required: true,
  },
  keyOnly: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:modelValue']);

const { getFieldIcon } = useFormFields();

const store = useStore();
/**
 * @type {import('vue').ComputedRef<CustomField[]>}
 */
const customFields = computed(() => store.state.form.customFields);

const options = ref(customFields.value);

const searchableFields = ['type', 'name', 'default_label'];
function onFilter(value, update) {
  if (value === '') {
    update(() => {
      options.value = customFields.value;
    });
    return;
  }

  update(() => {
    const needle = value.toLowerCase();
    options.value = customFields.value.filter((option) =>
      searchFields(needle, option, searchableFields),
    );
  });
}
</script>

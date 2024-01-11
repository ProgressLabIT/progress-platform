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
import { ref } from 'vue';
import { useFormFields } from '@/composables/form';
import searchFields from '@/lib/MultiFieldSearch';
import { api } from 'boot/axios';

/**
 * @typedef {{
 *  _key: string;
 *  type: string;
 *  name: string;
 *  default_label: string;
 *  default_hint: string;
 * }} FormField
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

const loading = ref(false);
/**
 * @type {import('vue').Ref<FormField[]>}
 */
const fields = ref([]);
const options = ref(fields.value);
(async () => {
  loading.value = true;

  const { data } = await api.get('field');
  fields.value = data;
  options.value = data;

  loading.value = false;
})();

const searchableFields = ['type', 'name', 'default_label'];
function onFilter(value, update) {
  if (value === '') {
    update(() => {
      options.value = fields.value;
    });
    return;
  }

  update(() => {
    const needle = value.toLowerCase();
    options.value = fields.value.filter((option) =>
      searchFields(needle, option, searchableFields),
    );
  });
}
</script>

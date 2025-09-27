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
    @update:model-value="(selection) => emit('select', selection)"
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

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useStore } from 'vuex';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import multiMatch from '@/lib/MultiFieldSearch.js';

// Props
const props = defineProps({
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
  userKeys: {
    type: Array,
    default: undefined,
  },
});

// Emits
const emit = defineEmits(['select']);

// Store
const store = useStore();

// Reactive data
const loading = ref(false);
const options = ref([]);
const search_fields = ref(['name', 'surname']);

// Computed properties
const origin_list = computed(() => {
  const baseList = props.operatorOnly
    ? store.getters.operator_list()
    : store.state.user?.user_list;

  return props.userKeys
    ? baseList.filter((user) => props.userKeys.includes(user._key))
    : baseList;
});

const placeholder_computed = computed(() => {
  return props.value ? null : props.placeholder;
});

// Methods
const initOptions = () => {
  options.value = [...origin_list.value];
};

const filter = (value, update) => {
  if (value === '') {
    update(() => {
      initOptions();
    });
    return;
  }
  update(() => {
    const needle = value.toLowerCase();
    options.value = origin_list.value.filter((option) => {
      return multiMatch(needle, option, search_fields.value);
    });
  });
};

// Lifecycle
onMounted(() => {
  if (props.loadData) {
    loading.value = true;
    store.dispatch('loadUsers').then(() => {
      initOptions();
      loading.value = false;
    });
  }
});
</script>

<style lang="sass">
.q-select:has(.user-avatar) .q-field__input
  min-width: 0px !important
</style>

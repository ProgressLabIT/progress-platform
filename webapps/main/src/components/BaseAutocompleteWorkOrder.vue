<template>
  <q-select
    use-input
    filled
    :loading="loading"
    :label-slot="!!label"
    :stack-label="stackLabel"
    :dense="dense"
    :hint="$t('work_order_autocomplete_hint')"
    :placeholder="placeholder_computed"
    :clearable="clearable"
    :options="options"
    :display-value="value?.wo_code"
    :option-value="key_only ? '_key' : null"
    @filter="filter"
    @clear="$emit('selection', null)"
    :model-value="value"
    input-debounce="500"
    :emit-value="key_only"
    :map-options="key_only"
    popup-content-style="width: 0px"
    @update:model-value="(selection) => $emit('select', selection)">
    <template #option="scope">
      <q-item
        v-bind="scope.itemProps"
        @click.stop="print"
        :class="{ 'text-low': scope.opt.status == 'closed' }">
        <q-item-section class="text-h4 highlight col-auto q-pr-md">
          {{ scope.opt.wo_code }}
        </q-item-section>
        <q-item-section>
          <q-item-label class="weight-bold">
            {{ scope.opt.product_code }}
          </q-item-label>
          <q-item-label caption lines="2" class="smaller text-uppercase">
            {{ scope.opt.product_description }}
          </q-item-label>
        </q-item-section>
        <q-item-section class="q-px-lg text-right col-2">
          <q-item-label>
            {{ scope.opt.qt_completed }}/{{ scope.opt.qt_planned }}
          </q-item-label>
          <q-item-label>
            <BaseProgressBar :data="scope.opt" />
          </q-item-label>
        </q-item-section>
        <q-item-section>
          <q-item-label lines="2">
            {{ scope.opt.project_code }}
          </q-item-label>
        </q-item-section>

      </q-item>
    </template>

    <template #label v-if="!!label">
      {{ label }}
    </template>

    <template #no-option>
      <div class="q-pa-md">
        No results
      </div>
    </template>
  </q-select>
</template>

<script>
import BaseProgressBar from '@/components/BaseProgressBar.vue'
export default {

  name: 'BaseAutocompletWorkOrder',

  components: {
    BaseProgressBar
  },

  props: {
    value: {
      type: [Object, String],
      deafult: null
    },

    label: {
      type: String,
      default: ''
    },

    key_only: {
      type: Boolean,
      default: false
    },

    dense: {
      type: Boolean,
      default: false
    },

    clearable: {
      type: Boolean,
      default: true
    },

    placeholder: {
      type: String,
      default: null
    },
  },

  data () {
    return {
      loading: false,
      origin_list: [],
      options: []
    }
  },

  computed: {
    placeholder_computed() {
      return this.value ? null : this.placeholder
    }
  },

  methods: {
    filter(value, update, abort) {
      if (value.length < 3) {
        abort()
        return
      }
      update(() => {
        this.loading = true
        const needle = value.toLowerCase()
        // No need of multiFieldSearch here. The api already checks all the necessary fields with a single search term.
        this.$api
          .get('work-order-archive', { params: { search: value, open: true }})
          .then((resp) => {
            this.options = resp.data
            this.loading = false
          })
      })
    },
  }
}
</script>

<style lang="css" scoped>
</style>

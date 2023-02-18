<template>
  <BaseDialog :show="show" @keyup.enter="update">
    <q-card class="surface2 q-pa-md" :style="`width: ${width}`">
      <q-card-section>
        <div class="text-h4 display highlight text-uppercase">
          {{ prompt }}
        </div>
        <q-input
          autofocus
          class="q-mt-md"
          input-class="text-body1"
          hide-bottom-space
          :type="input_type"
          :model-value="initial_value"
          @update:model-value="(val) => value = val">
        </q-input>
      </q-card-section>
      <q-card-actions align="between">
        <q-btn
          size="12px"
          flat
          color="theme-grey"
          @click="$emit('close')">
          {{ $t('cancel') }}
        </q-btn>
        <q-btn
          size="12px"
          flat
          v-if="value != initial_value"
          color="theme-blue"
          @click="update">
          {{ $t('save') }}
        </q-btn>
      </q-card-actions>
    </q-card>
  </BaseDialog>
</template>

<script>
import BaseDialog from '@/components/BaseDialog.vue'
export default {

  name: 'BasePrompt',

  components: {
    BaseDialog
  },

  props: {
    show: {
      type: Boolean,
      default: true
    },
    width: {
      type: String,
      default: '300px'
    },
    prompt: {
      type: String,
      default: () => this.$t('update')
    },
    input_type: {
      type: String,
      default: 'text'
    },
    initial_value: {
      required: true
    }
  },

  data () {
    return {
      value: null
    }
  },

  methods: {
    update() {
      this.$emit('update', this.value)
    }
  },

  created() {
    this.value = this.initial_value
  }
}
</script>

<style lang="css" scoped>
</style>

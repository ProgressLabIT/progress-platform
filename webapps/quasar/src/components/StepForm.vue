<template>
  <div>
    <div class="text-h5 text-uppercase q-mt-xl q-mb-md">
      {{ $t('phase.form_title') }}
    </div>

    <div id="field-list">
      <div
        v-for="(field, index) in input_fields"
        :key="index"
        class="q-mb-md">

        <q-input
          filled dense
          :disabled="!edit_mode"
          :type="field.type=='long' ? 'textarea' : 'text'"
          :placeholder="$capitalize($t('phase.field_name', { field_index: index + 1 }))"
          :name="`field-${index + 1}`"
          :model-value="field.name"
          @update:model-value="value => updateFieldName(index, value)">
        </q-input>

        <div
          v-if="edit_mode"
          class="row items-center low-text">
          <div class="col-5">
            <q-toggle
              :model-value="multilineCheck(field.type)"
              @update:model-value="value => updateFieldType(index, value)">
              <span class="text-body2">
                {{ $capitalize($t('phase.multiline_field')) }}
              </span>
            </q-toggle>
          </div>
          <div class="col-2 text-center">
            <q-icon
              v-if="index > 0"
              @mouseenter="onup=index"
              @mouseleave="onup=null"
              :name="`mdi-arrow-up-circle${onup!=index ? '-outline' : ''}`"
              :color="onup == index ? 'theme-blue' : false"
              size="xs"
              @click="moveUp(index)">
              <q-tooltip>
                move up
              </q-tooltip>
            </q-icon>
            <q-icon
              v-if="index < input_fields.length - 1"
              @mouseenter="ondown=index"
              @mouseleave="ondown=null"
              :name="`mdi-arrow-down-circle${ondown!=index ? '-outline' : ''}`"
              :color="ondown == index ? 'theme-blue' : false"
              size="xs"
              @click="moveDown(index)">
              <q-tooltip>
                Move down
              </q-tooltip>
            </q-icon>

          </div>
          <div class="q-ml-auto">
            <div
              v-if="confirming_delete != index"
              class="hover-red"
              @click="confirming_delete = index">
              <span class="text-body2 q-mr-xs">
                {{ $capitalize($t('phase.delete_field')) }}
              </span>
              <q-icon name="mdi-close" size="xs" />
            </div>
            <div v-else class="surface2">
              <q-btn
                padding="xs sm"
                icon="mdi-delete"
                color="theme-red"
                size="xs"
                @click.stop="deleteField(index)">
              </q-btn>
              <span class="text-body-2 q-mx-lg">
                {{ $capitalize($t('confirm_question')) }}
              </span>
              <q-btn
                padding="xs sm"
                icon="mdi-close"
                color="theme-grey"
                size="xs"
                @click.stop="confirming_delete=null">
              </q-btn>
            </div>
          </div>
        </div>
      </div>
    </div>

    <q-btn
      color="theme-blue"
      size="12px"
      class="q-mt-md"
      v-if="edit_mode"
      @click="addField">
      + {{ $capitalize($t('phase.add_field')) }}
    </q-btn>
  </div>
</template>

<script>
export default {

  name: 'StepForm',

  props: ['phase_index', 'step_index', 'edit_mode'],

  data() {
    return {
      confirming_delete: null,
      onup: null,
      ondown: null
    }
  },

  computed: {

    product_key() {
      return this.$route.params.item_key
    },

    input_fields: {
      get() {
        const procedure = this.$store.state.process.temp[this.phase_index].steps
        const current_step = procedure[this.step_index]
        return current_step.input_fields
      },
      set(value) {
        let phase_index = this.phase_index
        let step_index = this.step_index

        this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'input_fields', value })
      }
    }
  },

  methods: {

    multilineCheck(field_type) {
      switch (field_type) {
        case 'short': return false
        case 'long': return true 
      }
    },

    addField() {
      let phase_index = this.phase_index
      let step_index = this.step_index

      // Handle cases in which input_fields is null
      let new_field_list = this.input_fields ? this.input_fields : []

      new_field_list.push({ type: 'short', name: ''})
      this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'input_fields', value: new_field_list })
    },

    updateFieldName(index, text) {
      let phase_index = this.phase_index
      let step_index = this.step_index
      let new_field_list = this.input_fields
      new_field_list[index].name = text
      this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'input_fields', value: new_field_list })
    },

    updateFieldType(index, multiline) {
      let phase_index = this.phase_index
      let step_index = this.step_index
      let new_field_list = this.input_fields

      let new_type = multiline ? 'long' : 'short'
      new_field_list[index].type = new_type

      this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'input_fields', value: new_field_list })
    },

    moveUp(index) {
      const moved = this.input_fields.splice(index, 1)[0]
      this.input_fields.splice(index - 1, 0, moved)
    },

    moveDown(index) {
      const moved = this.input_fields.splice(index, 1)[0]
      this.input_fields.splice(index + 1, 0, moved)
    },

    deleteField(index) {
      let phase_index = this.phase_index
      let step_index = this.step_index
      let new_field_list = this.input_fields
      new_field_list.splice(index, 1)
      this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'input_fields', value: new_field_list })
      this.confirming_delete = null
    }
  }
};
</script>

<style lang="css">
</style>

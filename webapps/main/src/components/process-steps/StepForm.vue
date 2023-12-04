<template>
  <div>
    <div class="text-h5 text-uppercase q-mt-xl q-mb-md">
      {{ $t('phase.form_title') }}
    </div>

    <div id="field-list">
      <div
        v-for="(field, index) in stepModel.input_fields"
        :key="index"
        class="q-mb-md"
      >
        <q-input
          v-model="field.name"
          filled
          dense
          :disable="!editMode"
          :type="field.type === 'long' ? 'textarea' : 'text'"
          :placeholder="$capitalize($t('phase.field_name', { field_index: index + 1 }))"
          :name="`field-${index + 1}`"
        />

        <div
          v-if="editMode"
          class="row items-center low-text"
        >
          <div class="col-5">
            <q-toggle
              :model-value="field.type === 'long'"
              @update:model-value="(value) => {
                field.type = value ? 'long' : 'short'
              }"
            >
              <span class="text-body2">
                {{ $capitalize($t('phase.multiline_field')) }}
              </span>
            </q-toggle>
          </div>

          <div class="col-2 text-center">
            <q-icon
              v-if="index > 0"
              :name="`mdi-arrow-up-circle${onUpIndex !== index ? '-outline' : ''}`"
              :color="onUpIndex === index ? 'theme-blue' : undefined"
              size="xs"
              @click="moveUp(index)"
              @mouseenter="onUpIndex = index"
              @mouseleave="onUpIndex = null"
            >
              <q-tooltip>
                move up
              </q-tooltip>
            </q-icon>

            <q-icon
              v-if="index < stepModel.input_fields.length - 1"
              :name="`mdi-arrow-down-circle${onDownIndex !== index ? '-outline' : ''}`"
              :color="onDownIndex === index ? 'theme-blue' : undefined"
              size="xs"
              @click="moveDown(index)"
              @mouseenter="onDownIndex = index"
              @mouseleave="onDownIndex = null"
            >
              <q-tooltip>
                Move down
              </q-tooltip>
            </q-icon>
          </div>
          <div class="q-ml-auto">
            <div
              v-if="confirmingDeleteIndex !== index"
              class="hover-red"
              @click="confirmingDeleteIndex = index"
            >
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
                @click.stop="deleteField(index)"
              />
              <span class="text-body-2 q-mx-lg">
                {{ $capitalize($t('confirm_question')) }}
              </span>
              <q-btn
                padding="xs sm"
                icon="mdi-close"
                color="theme-grey"
                size="xs"
                @click.stop="confirmingDeleteIndex = null"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <q-btn
      v-if="editMode"
      color="theme-blue"
      size="12px"
      icon="mdi-plus"
      :label="$t('add_field')"
      class="q-mt-md"
      @click="addField"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  editMode: {
    type: Boolean,
    required: true
  }
})

const stepModel = defineModel('step', { type: Object })

const confirmingDeleteIndex = ref(null)
const onUpIndex = ref(null)
const onDownIndex = ref(null)

function move(index, delta) {
  const [moved] = stepModel.value.input_fields.splice(index, 1)
  stepModel.value.input_fields.splice(index + delta, 0, moved)
}
const moveUp = (index) => move(index, -1)
const moveDown = (index) => move(index, 1)

function addField() {
  stepModel.value.input_fields.push({ type: 'short', name: '' })
}

function deleteField(index) {
  stepModel.value.input_fields.splice(index, 1)
  confirmingDeleteIndex.value = null
}
</script>

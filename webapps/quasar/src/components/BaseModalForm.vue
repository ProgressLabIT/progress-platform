<template>
  <q-dialog
    v-model="show"
    square no-backdrop-dismiss no-shake :style="{ ...$theme }">
    <q-card class="surface1 q-pa-md" :style="{ maxWidth: max_width }">

      <!-- DIALOG TITLE -->
      <q-card-section class="text-h3 display weight-medium">
        <slot name="title"></slot>
      </q-card-section>

      <q-card-section>
        <q-form @submit="$emit('submit')" v-model="valid">
          <slot name="form"></slot>
          <div class="row q-mt-md q-col-gutter-md">
            <slot name="actions">
              <q-btn
                class="col full-width"
                color="theme-blue"
                @click="$emit('submit')">
                {{ $t('save') }}
              </q-btn>

              <q-btn
                class="col full-width"
                color="theme-grey"
                @click="$emit('cancel')">
              </q-btn>

            </slot>
          </div>
        </q-form>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script>
export default {

  name: 'BaseModalForm',

  props: {
    show: {
      type: Boolean,
      default: true
    },
    max_width: {
      type: String,
      default: '500px'
    }
  },

  data () {
    return {
      saving: false,
      valid: true
    }
  },
}
</script>

<style>
</style>

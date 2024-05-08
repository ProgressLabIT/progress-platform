<template>
  <q-item class="q-py-md" :clickable="clickable">
    <q-item-section avatar>
      <q-icon flat :name="serial.icon || 'mdi-help'" size="lg" />
    </q-item-section>
    <q-item-section>
      <q-item-label class="row items-center">
        <span class="smaller text-body2 text-uppercase low-text q-ml-md">
          <span class="q-mr-sm">
            {{ serial.serial }}
          </span>
          <span>#{{ serial._key }}</span>
        </span>
        <div class="col q-ml-xl">
          <q-btn
            flat
            round
            icon="mdi-pencil"
            @click.stop="show_serial_update = true"
          >
            <q-tooltip>{{ $capitalize($t('edit')) }}</q-tooltip>
          </q-btn>
        </div>
      </q-item-label>
    </q-item-section>

    <!-- SERIAL EDIT DIALOG -->
    <SerialForm
      :show="show_serial_update"
      :serial="serial"
      mode="edit"
      @close="show_serial_update = false"
    >
    </SerialForm>
  </q-item>
</template>

<script>
import SerialForm from 'app/src/components/traceability/SerialForm.vue';

export default {
  name: 'SerialHeader',

  components: {
    SerialForm,
  },

  props: {
    serial: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      show_serial_update: false,
    };
  },
};
</script>

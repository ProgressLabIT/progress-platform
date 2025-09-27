<template>
  <BaseDialog :show="show" :maximized="maximized" @close="onClose">
    <q-card class="surface1 q-pa-md" :style="{ maxWidth: maxWidth, minWidth: minWidth }">
      <!-- DIALOG TITLE -->
      <q-card-section class="text-h3 display weight-medium">
        <slot name="title"></slot>
      </q-card-section>

      <q-card-section>
        <slot name="form"></slot>
      </q-card-section>

      <q-card-section>
        <div class="row q-mt-md q-col-gutter-md">
          <slot name="actions">
            <div class="col-6">
              <q-btn
                class="full-width"
                color="theme-blue"
                :loading="loading"
                :disable="!enableSave"
                @click="emit('submit')"
              >
                {{ $t('save') }}
              </q-btn>
            </div>
            <div class="col-6">
              <q-btn
                class="full-width"
                color="theme-grey"
                @click="emit('cancel')"
              >
                {{ $t('cancel') }}
              </q-btn>
            </div>
          </slot>
        </div>
      </q-card-section>
    </q-card>
  </BaseDialog>
</template>

<script setup>
import { useRouter } from 'vue-router';
import BaseDialog from '@/components/BaseDialog.vue';

const props = defineProps({
  show: { type: Boolean, default: true },
  maxWidth: { type: String, default: '800px' },
  minWidth: { type: String, default: '500px' },
  loading: { type: Boolean, default: false },
  maximized: { type: Boolean, default: false },
  enableSave: { type: Boolean, default: true },
  handleClose: { type: Function, default: undefined },
});

const emit = defineEmits(['submit', 'cancel']);

const router = useRouter();

function onClose() {
  if (props.handleClose === undefined) {
    router.back();
  } else {
    props.handleClose();
  }
}
</script>

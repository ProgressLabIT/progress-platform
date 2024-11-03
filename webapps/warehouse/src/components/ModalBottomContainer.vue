<template>
  <div class="q-pa-md q-gutter-sm">
    <q-dialog
      :model-value="show"
      position="bottom"
      fixed="true"
      backdrop-filter="brightness(60%)"
      @escape-key="$emit('close')"
      @hide="$emit('close')"
      @click="drawerModel = false"
    >
      <q-card class="background q-pa-sm">
        <!-- SCREEN HEADER -->
        <div class="row justify-start items-center q-px-sm text-high">
          <slot name="header"></slot>

          <slot name="close">
            <q-btn flat dense @click="$emit('close')">
              <q-icon size="xs" name="mdi-close" class="text-low" />
            </q-btn>
          </slot>
        </div>

        <!-- WINDOW CONTAINER
      <q-card
        class="surface1 shadow-6 q-mx-sm scroll"
        :style="`height: ${card_height}px`"
      > -->
        <q-card
          class="surface1 shadow-6 q-mx-sm scroll"
          :style="`height: ${card_height}px`"
        >
          <slot name="content"></slot>
        </q-card>
      </q-card>
    </q-dialog>
  </div>
</template>

<script>
import { useDrawer } from '@/composables/drawer';
import CSSVars from '@/mixins/CSSVars.js';

export default {
  name: 'ModalBottomContainer',

  mixins: [CSSVars],
  props: {
    show: {
      type: Boolean,
      required: true,
    },
  },
  emits: ['close'],

  setup() {
    const { drawerModel } = useDrawer();

    return {
      drawerModel,
    };
  },

  /*computed: {
    card_height() {
      return this.$q.screen.height - 52;
    },
  },*/
};
</script>

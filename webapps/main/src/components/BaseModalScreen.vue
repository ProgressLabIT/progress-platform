<template>
  <q-dialog
    :model-value="show"
    maximized
    no-backdrop-dismiss
    no-route-dismiss
    :no-esc-dismiss="noEscDismiss"
    no-shake
    square
    transition-show="scale"
    transition-hide="scale"
    :style="CSSVars"
    @escape-key="$emit('close')"
    @hide="$emit('close')"
    @click="show_drawer = false"
  >
    <q-card class="background q-pa-sm">
      <!-- SCREEN HEADER -->
      <div class="row justify-start items-center q-px-sm text-high">
        <slot name="menu">
          <q-btn
            flat
            icon="mdi-menu"
            padding="none"
            @click="show_drawer = true"
          >
          </q-btn>
        </slot>

        <slot name="header"></slot>

        <slot name="close">
          <q-btn flat dense @click="$emit('close')">
            <q-icon size="xs" name="mdi-close" class="text-low" />
          </q-btn>
        </slot>
      </div>

      <!-- WINDOW CONTAINER -->
      <q-card
        class="surface1 shadow-6 q-mx-sm scroll"
        :style="`height: ${card_height}px`"
      >
        <slot name="content"></slot>
      </q-card>
    </q-card>
  </q-dialog>
</template>

<script>
import CSSVars from '@/mixins/CSSVars.js';
import drawer from '@/mixins/drawer.js';

export default {
  name: 'BaseModalScreen',
  mixins: [CSSVars, drawer],
  props: {
    show: {
      type: Boolean,
      required: true,
    },
    noEscDismiss: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['close'],

  computed: {
    card_height() {
      return this.$q.screen.height - 52;
    },
  },
};
</script>

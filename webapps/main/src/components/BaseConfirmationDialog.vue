<template>
  <!-- TODO: Migrate to Quasar if the component will end up being used -->
  <v-dialog
    :value="show"
    :overlay-color="$theme.background"
    width="unset"
    :max-width="max_width"
    overlay-opacity=".5"
    @keydown.esc="$emit('close')"
    @input="$emit('close')"
  >
    <v-card>
      <v-card-title>
        <slot></slot>
      </v-card-title>
      <v-card-actions>
        <v-slot name="actions" style="width: 100%">
          <v-container>
            <v-row class="mx-0" justify="space-between">
              <v-btn
                :color="confirm_color || $theme.blue"
                @click="confirm_action()"
              >
                {{ confirm_prompt || $t('confirm') }}
              </v-btn>
              <v-btn
                :color="cancel_color || $theme.grey"
                @click="$emit('close')"
              >
                {{ cancel_prompt || $t('cancel') }}
              </v-btn>
            </v-row>
          </v-container>
        </v-slot>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
/* eslint-disable vue/prop-name-casing */
export default {
  name: 'BaseConfirmationDialog',

  props: {
    show: {
      type: Boolean,
      required: true,
    },
    confirm_color: {
      type: String,
      default: undefined,
    },
    confirm_prompt: {
      type: String,
      default: undefined,
    },
    confirm_action: {
      type: Function,
      required: true,
    },
    cancel_color: {
      type: String,
      default: undefined,
    },
    cancel_prompt: {
      type: String,
      default: undefined,
    },
    max_width: {
      type: String,
      default: '60%',
    },
  },

  emits: ['close'],
};
</script>

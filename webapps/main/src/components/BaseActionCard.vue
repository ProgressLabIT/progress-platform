<template>
  <q-card class="surface2 q-pa-md" style="min-width: 400px;">
    <slot name="title">
      <q-card-section v-if="title">
        <div class="text-h3 display highlight">
          {{ title }}
        </div>
      </q-card-section>
    </slot>

    <q-card-section>
      <slot></slot>
    </q-card-section>

    <q-card-section class="row justify-between">
      <slot name="actions">
        <q-btn
          color="theme-blue"
          @click="$emit('save')">
          {{ save_label ?? $t('save') }}
        </q-btn>
        <q-btn
          color="theme-grey"
          @click="$emit('cancel')">
          {{ cancel_label ?? $t('cancel') }}
        </q-btn>
      </slot>
    </q-card-section>
  </q-card>
</template>

<script>
export default {

  name: 'BaseActionCard',

  props: {
    title: String,
    save_label: String,
    cancel_label: String
  },

  data () {
    return {

    }
  }
}
</script>

<style lang="css" scoped>
</style>

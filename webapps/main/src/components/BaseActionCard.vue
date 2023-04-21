<template>
  <q-card class="surface2 q-pa-md" style="min-width: 400px;">
    <slot name="title">
      <q-card-section>
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
          :label="$t('save')"
          @click="$emit('save')">
        </q-btn>
        <q-btn
          color="theme-grey"
          :label="$t('cancel')"
          @click="$emit('cancel')">
        </q-btn>
      </slot>
    </q-card-section>
  </q-card>
</template>

<script>
export default {

  name: 'BaseActionCard',

  props: {
    title: {
      type: String
    }
  },

  data () {
    return {

    }
  }
}
</script>

<style lang="css" scoped>
</style>

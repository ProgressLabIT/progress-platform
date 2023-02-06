<template>
  <div class="fit flex-center">
    <div class="text-h3 display highlight text-uppercase">
      {{ title ? title : $t('loading_text') }}
    </div>
    <q-circular-progress
      indeterminate
      size="40px"
      color="theme-blue"
      class="q-mt-md">
    </q-circular-progress>
  </div>
</template>

<script>
export default {

  name: 'LoadingSignal',

  props: {
    title: {
      type: String,
      default: null
    },
  }
}
</script>

<style lang="css" scoped>
</style>

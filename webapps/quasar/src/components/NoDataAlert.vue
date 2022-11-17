<template>
  <div class="fit column flex-center">
    <q-icon size="xl" color="low" name="mdi-alert-circle-outline" />
    <div class="text-center q-mt-md text-uppercase">
      <div class="text-h3">
        <slot>No data</slot>
      </div>
    </div>
  </div>
</template>

<script>
export default {

  name: 'NoDataAlert',

}
</script>

<style lang="css" scoped>
</style>

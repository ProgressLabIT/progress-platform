<template>
  <div class="absolute-center text-center">
    <q-icon size="xl" color="low" name="mdi-alert-circle-outline" />
    <div class="text-uppercase q-mt-sm">
      <div class="text-h3">
        <slot>No data</slot>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NoDataAlert',
};
</script>

<style lang="css" scoped></style>

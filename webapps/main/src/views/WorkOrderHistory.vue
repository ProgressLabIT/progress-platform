<template>
  <div class="q-pa-lg">
    <q-virtual-scroll
      class="full-height"
      :items="items"
      v-slot="{ item, index }"
    >
      <q-item :key="index">
        <q-item-section v-for="n in 3" :key="n">
          {{ n }} {{ item }}
        </q-item-section>
      </q-item>
    </q-virtual-scroll>
  </div>
</template>

<script>
export default {
  name: 'WorkOrderHistory',

  data() {
    return {
      items: Array(20).fill('test'),
    };
  },
};
</script>

<style lang="css" scoped></style>

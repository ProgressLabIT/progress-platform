<template>
  <q-scroll-area class="col">
    <q-list>
      <q-item
        v-for="product in products"
        :key="product._key"
        clickable
        dense
        class="content-card q-my-xs q-py-sm"
        :class="getProductColor(product)"
        @click="$emit('select', product)"
      >
        <q-item-section side>
          <q-icon :name="product.traceability_level ? 'mdi-cube-scan' : 'mdi-apps'" />
        </q-item-section>
        <q-item-section>
          <q-item-label class="highlight">{{ product.code }}</q-item-label>
          <q-item-label caption>{{ product.description }}</q-item-label>
        </q-item-section>
      </q-item>
    </q-list>
  </q-scroll-area>
</template>

<script setup>
defineProps({
  products: {
    type: Array,
    required: true
  }
});

defineEmits(['select']);

function getProductColor(product) {
  return product.traceability_level ? 'bg-green-backdrop' : 'bg-blue-backdrop';
}
</script>

<style lang="sass" scoped>
.content-card
  border-radius: 5px
  border: 1px solid transparent
</style>

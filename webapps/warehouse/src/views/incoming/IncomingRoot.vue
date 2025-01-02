<template>
  <template v-if="nav.loading" />
  <router-view v-else/>
</template>

<script setup>
import { useNavStore } from 'app/src/stores/navigation';
import { useListsStore } from 'app/src/stores/lists';
const nav = useNavStore();
const lists = useListsStore();

lists.loadLists();
</script>

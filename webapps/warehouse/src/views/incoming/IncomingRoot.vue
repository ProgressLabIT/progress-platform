<template>
  <template v-if="nav.loading" />
  <router-view v-else/>
</template>

<script setup>
import { useListsStore } from 'stores/lists'
import { useNavStore } from 'app/src/stores/navigation';
import { useQuasar } from 'quasar';

const lists = useListsStore();
const nav = useNavStore()
const $q = useQuasar()

nav.loading = true
$q.loading.show()
lists.loadData().then(() => setTimeout(() => {
  nav.loading = false;
  $q.loading.hide();
}, 300));
</script>

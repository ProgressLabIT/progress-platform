<template>
  <div class="absolute-full scroll">
    <iframe id="iframe" :src="src" frameborder="0" ref="streamlitIframe"></iframe>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useStore } from 'vuex';

const store = useStore();

const src = computed(() => {
  const domain = window.location.hostname;
  const protocol = window.location.protocol;
  const sessionData = store.state.session;
  const sessionDataStr = JSON.stringify(sessionData);
  const encodedSession = btoa(sessionDataStr);
  return `${protocol}//reporting.${domain}?session=${encodedSession}`;
});


onMounted(() => {
  console.log(src.value);
});
</script>

<style lang="sass" scoped>
#iframe
  height: 100%
  width: 100%
</style>

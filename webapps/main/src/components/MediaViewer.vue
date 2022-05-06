<template>
  <BaseModalScreen v-bind="{show}" @close="$emit('close')">

    <template v-slot:header>
      <div class="ml-4 py-1 medium highlight">{{ media_name }}</div>
    </template>

    <template v-slot:content v-if="show">
      <v-img contain height="100%"
        v-if="hasImageExtension()" 
        :src="media_src">
      </v-img>
      <embed v-else
        :key="media_src"
        :src="media_src + '#toolbar=0'"
        width="100%"
        height="100%" />
    </template>
  </BaseModalScreen>
</template>

<script>
import BaseModalScreen from '@/components/BaseModalScreen.vue'
export default {

  name: 'MediaViewer',

  components: {
    BaseModalScreen
  },

  props: ['show', 'media_name', 'media_src'],

  data() {
    return {
      image_extensions: ['png', 'jpeg', 'jpg']
    }
  },

  methods: {
    hasImageExtension() {
      // const ext = typeof this.media_name == "string" 
      //   ? this.media_name.split('.')[this.media_src.length -1]
      //   : null
      // return ext
      return this.media_src
        ? this.image_extensions.some( e => this.media_src.endsWith(e) )
        : null
    },

    escClose (event) {
      if (event.key === 'Escape') {
        this.$emit('close')
      }
    }
  },

  created () {
    document.addEventListener('keyup', this.escClose)
  },

  beforeDestroy () {
    document.removeEventListener('keyup', this.escClose)
  }

}
</script>

<style lang="css" scoped>
</style>

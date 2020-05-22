<template>
  <v-container class="pa-12">
    <BaseUserAvatar 
      :user="user"
      size="100" 
      :show_name="false">
    </BaseUserAvatar>
    <v-row v-for="(value, key) in user" :key="key">
      {{ key }}: {{ value }}
    </v-row>
  </v-container>  
</template>

<script>
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'

export default {

  name: 'UserInfoScreen',

  components: { BaseUserAvatar },

  props: {
    user: {
      type: Object,
      required: true
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
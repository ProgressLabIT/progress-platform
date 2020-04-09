<template>
  <v-row dense align="center" :class="name_first ? 'flex-row-reverse' : ''">
    <v-col cols="auto">
      <v-avatar :color="$theme.grey" :size="size">
        <v-img :src="avatar_src">
          <template v-slot:placeholder>
            <v-row align="end" justify="center">{{ initials }}</v-row>
          </template>
        </v-img>
      </v-avatar>
    </v-col>
    <v-col cols="auto">
      <component v-if="show_name" :is="name_el" :class="name_class">
        {{ full_name | capitalize_all }}
      </component>
    </v-col>
  </v-row>
</template>

<script>
export default {

  name: 'BaseUserAvatar',

  props: {
    name_first: {
      type: Boolean,
      default: false
    },

    user: {
      type: Object,
      required: true
    },

    size: {
      type: [String, Number],
      default: 32,
    },
    
    show_name: {
      type: Boolean,
      default: true
    },
    
    name_el: {
      type: String,
      default: 'span'
    },
    
    name_class: {
      type: String,
      default: 'body-2'
    }
  },

  data() {
    return {
      base_path: '/media/user/'
    }
  },

  computed: {
    avatar_src() {
      return this.base_path + (this.user.name + this.user.surname).replace(/\s+/g, '') + '.jpg'
    },

    initials() {
      return this.user.name[0].toUpperCase() + this.user.surname[0].toUpperCase()
    },

    full_name() {
      return this.user.name + ' ' + this.user.surname
    },
  }
}
</script>

<style lang="css" scoped>
</style>
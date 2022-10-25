<template>
  <div class="row align-center" :class="name_first ? 'reverse' : ''">
    <div class="col-auto">
      <q-avatar color="theme-grey" :size="size">
        <q-img :src="avatar_src" :alt="initials" />
      </q-avatar>
    </div>
    <div class="col-auto">
      <component
        v-if="show_name"
        :is="name_el"
        :class="name_class"
        :style="name_style">
        {{ full_name }}
      </component>
    </div>
  </div>
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
      type: String,
      default: '32px',
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
      default: 'body-2 uppercase'
    },

    name_style: {
      type: String
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

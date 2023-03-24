<template>
  <div
    class="row items-center"
    :class="name_first ? ' reverse' : ''">
    <q-avatar
      color="theme-grey"
      :size="size"
      v-if="initials"
      class="weight-bold"
      font-size=".4em">
      <q-img
        :src="avatar_src"
        :alt="initials"
        :style="avatar_style">
        <template #error>
          <div class="absolute-center bg-theme-grey" v-if="initials">{{ initials }}</div>
          <q-icon v-else name="mdi-account-circle" :size="size"/>
        </template>
      </q-img>
    </q-avatar>
    <div class="column col-auto q-mx-md" v-if="show_name">
      <slot name="name">
        <div
          :class="name_class"
          :style="name_style">
          {{ full_name }}
        </div>
      </slot>

      <slot
        name="subtitle"
        :class="subtitle_class"
        :style="subtitle_style">
      </slot>
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
      default: 'div'
    },
    
    name_class: {
      type: String,
      default: 'text-body2'
    },

    name_style: {
      type: String
    },

    subtitle_class: {
      type: String,
      default: 'text-body2'
    },

    subtitle_style: {
      type: String
    }
  },

  data() {
    return {
      base_path: '/media/user/',
      avatar_style: {
        height: this.size,
        width: this.size,
        borderRadius: '100%'
      }
    }
  },

  computed: {
    avatar_src() {
      return this.base_path + (this.user.name + this.user.surname).replace(/\s+/g, '') + '.jpg'
    },

    initials() {
      try {
        return this.user.name[0].toUpperCase() + this.user.surname[0].toUpperCase()
      } catch { return 'N/A' }
    },

    full_name() {
      return this.$capitalizeAll(this.user.name + ' ' + this.user.surname) || ''
    },
  }
}
</script>

<style lang="sass" scoped>
</style>

<template>
  <div class="row items-center" :class="name_first ? ' reverse' : ''">
    <q-avatar
      color="theme-grey"
      :size="size"
      v-if="initials && showAvatar"
      class="weight-bold"
      font-size=".4em"
    >
      <q-img :src="avatar_src" :alt="initials" :style="avatar_style">
        <template #error>
          <div class="absolute-center bg-theme-grey" v-if="initials">
            {{ initials }}
          </div>
          <q-icon v-else name="mdi-account-circle" :size="size" />
        </template>
      </q-img>
    </q-avatar>

    <div
      v-if="show_name && showAvatar"
      :class="dense ? 'q-mx-xs' : 'q-mx-sm'"
    ></div>

    <div class="column col-auto" v-if="show_name">
      <slot name="name">
        <div :class="name_class" :style="name_style">
          {{ full_name }}
        </div>
      </slot>

      <slot name="subtitle"> </slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BaseUserAvatar',

  props: {
    dense: {
      type: Boolean,
      default: false,
    },

    name_first: {
      type: Boolean,
      default: false,
    },

    user: {
      type: Object,
      required: true,
    },

    size: {
      type: String,
      default: '32px',
    },

    showAvatar: {
      type: Boolean,
      default: true,
    },

    show_name: {
      type: Boolean,
      default: true,
    },

    name_el: {
      type: String,
      default: 'div',
    },

    name_class: {
      type: String,
      default: 'text-body2',
    },

    name_style: {
      type: String,
      default: undefined,
    },
  },

  data() {
    return {
      base_path: '/media/user/',
      avatar_style: {
        height: this.size,
        width: this.size,
        borderRadius: '100%',
      },
    };
  },

  computed: {
    avatar_src() {
      return this.user.name && this.user.surname
        ? (
            this.base_path +
            (this.user.name + this.user.surname).replace(/\s+/g, '') +
            '.jpg'
          ).toLowerCase()
        : 'N/A';
    },

    initials() {
      try {
        return (
          this.user.name[0].toUpperCase() + this.user.surname[0].toUpperCase()
        );
      } catch {
        return 'N/A';
      }
    },

    full_name() {
      return (
        this.$capitalizeAll(this.user.name + ' ' + this.user.surname) || ''
      );
    },
  },
};
</script>

<style lang="sass" scoped></style>

<template>
  <div class="row inline items-center" :class="name_first ? ' reverse' : ''">
    <q-avatar
      v-if="initials && showAvatar"
      :color="imgError ? 'theme-grey' : undefined"
      :size="computed_size"
      class="weight-bold"
      font-size=".4em"
    >
      <img
        v-if="!imgError"
        :src="avatar_src"
        :alt="initials"
        :style="avatar_style"
        @error="imgError = true"
      >
      <template v-else>
        <span v-if="initials">{{ initials }}</span>
        <q-icon v-else name="mdi-account-circle" :size="computed_size" />
      </template>
    </q-avatar>

    <div
      v-if="show_name && showAvatar"
      :class="dense ? 'q-mx-xs' : 'q-mx-sm'"
    ></div>

    <div v-if="show_name" class="column col-auto">
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
      default: undefined,
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
      imgError: false,
    };
  },

  watch: {
    user() {
      this.imgError = false;
    },
  },

  computed: {
    avatar_src() {
      return this.user?.name && this.user?.surname
        ? (
            this.base_path +
            (this.user?.name + this.user?.surname).replace(/\s+/g, '') +
            '.jpg'
          ).toLowerCase()
        : 'NA.jpg';
    },

    avatar_style() {
      return {
        height: this.computed_size,
        width: this.computed_size,
        borderRadius: '100%',
      };
    },

    initials() {
      try {
        return (
          this.user?.name[0].toUpperCase() + this.user?.surname[0].toUpperCase()
        );
      } catch {
        return 'N/A';
      }
    },

    full_name() {
      return this.$capitalizeAll(
        this.user ? this.user.name + ' ' + this.user.surname : 'NA'
      );
    },

    computed_size() {
      return this.dense ? '26px' : this.size;
    },
  },
};
</script>

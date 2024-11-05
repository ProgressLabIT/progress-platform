<template>
  <q-linear-progress
    animation-speed="300"
    :value="progress"
    :color="color.foreground"
    :track-color="color.background"
    :buffer="1"
    :size="size"
  />
</template>

<script>
export default {
  name: 'JobTimerProgressBar',

  props: {
    data: {
      type: Object,
      required: true,
    },
    size: {
      type: String,
      default: '4px',
    },
  },

  computed: {
    progress() {
      if (this.data.consumed > this.data.total) {
        return 100;
      }
      return this.data.consumed / this.data.total;
    },

    color() {
      const background = this.data.active
        ? this.data.consumed > this.data.total
          ? 'red-backdrop'
          : 'blue-backdrop'
        : 'grey-backdrop';
      const foreground =
        this.data.consumed > this.data.total
          ? this.data.active
            ? 'theme-red'
            : 'red-backdrop'
          : this.data.active
            ? 'theme-blue'
            : 'theme-grey';
      return { foreground, background };
    },
  },
};
</script>

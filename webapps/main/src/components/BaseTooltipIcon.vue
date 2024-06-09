<template>
  <slot name="before"></slot>
  <q-icon
    :name="icon"
    :size="icon_size"
    class="q-mx-xs hover-color"
    :style="hoverColor"
    @click.stop="emit"
  >
    <q-tooltip
      :delay="Number(100)"
      :anchor="anchor"
      :self="self"
      :transition-show="transition_show"
      :transition-hide="transition_hide"
      transition-duration="200"
      :style="`background-color: ${color}`"
      class="text-body2"
    >
      {{ $capitalize(tooltip) }}
    </q-tooltip>
  </q-icon>
  <slot name="after"></slot>
</template>

<script>
export default {
  name: 'BaseTooltipIcon',
  props: {
    icon: {
      type: String,
      required: true,
    },
    icon_size: {
      type: String,
      default: 'sm',
    },
    tooltip: {
      type: String,
      required: true,
    },
    color: {
      type: String,
      default: 'grey',
    },
    anchor: {
      type: String,
      default: 'top middle',
    },
    self: {
      type: String,
      default: 'bottom middle',
    },
    transition_show: {
      type: String,
      default: 'scale',
    },
    transition_hide: {
      type: String,
      default: 'scale',
    },
  },

  emits: ['iconClick'],

  data() {
    return {};
  },
  computed: {
    hoverColor() {
      return {
        '--hover-color': this.color,
      };
    },
  },

  methods: {
    /*
    On the parent element, this allows to bubble up the click event correctly
    with the event name equal to the tooltip text passed down
    */
    emit() {
      this.$emit('iconClick');
    },
  },
};
</script>

<style lang="css" scoped>
.hover-color:hover {
  color: var(--hover-color);
}
</style>

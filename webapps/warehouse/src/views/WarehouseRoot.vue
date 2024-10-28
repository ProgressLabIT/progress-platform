<template>
  <div id="q-app">
    <div class="q-pa-md">
      <div class="text-subtitle1 q-py-xl text-center">
        Play with the drawer on bottom
      </div>

      <q-card
        class="slide-drawer slide-drawer--bottom text-white fixed-bottom column no-wrap"
        :class="`slide-drawer--open-${drawerMode}`"
        :style="drawerStyle"
      >
        <q-card-section
          v-touch-pan.mouse.vertical="slideDrawer"
          class="slide-drawer__handler--horizontal row flex-center q-pa-sm q-gutter-x-md"
        >
          <span class="text-caption">Drag drawer</span>
          <div class="cursor-pointer" @click="cycleDrawer"></div>
          <span class="text-caption">or click pill</span>
        </q-card-section>

        <q-card-section class="col">
          <div class="text-h6">Our Changing Planet</div>
          <div class="text-subtitle2">by John Doe</div>
          <div>{{ lorem }}</div>
        </q-card-section>

        <q-card-section v-if="drawerMode !== 'handler'" class="col">
          <div class="text-h6">
            Our Changing Planet - only shown when drawer is open
          </div>
          <div class="text-subtitle2">by John Doe</div>
          <div>{{ lorem }}</div>
        </q-card-section>
      </q-card>
    </div>
  </div>
</template>

<script>
const drawerMinHeight = 36;
const drawerTopOffset = 100;
const drawerOpenRatioHalf = 50;

export default {
  name: 'WarehouseRoot',

  data() {
    return {
      lorem:
        'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.',
      drawerPos: drawerMinHeight,
    };
  },

  computed: {
    drawerMaxHeight() {
      return Math.max(0, this.$q.screen.height - drawerTopOffset);
    },

    drawerOpenRatio() {
      return Math.round(
        (Math.max(0, this.drawerPos - drawerMinHeight) /
          Math.max(1, this.drawerMaxHeight - drawerMinHeight)) *
          100
      );
    },

    drawerStyle() {
      return {
        height: `${this.drawerMaxHeight}px`,
        transform: `translateY(${-this.drawerPos}px)`,
      };
    },

    drawerMode() {
      if (this.drawerOpenRatio > drawerOpenRatioHalf) {
        return 'full';
      }

      return this.drawerOpenRatio > 0 ? 'half' : 'handler';
    },
  },

  beforeUnmount() {
    clearTimeout(this.animateTimeout);
  },

  methods: {
    slideDrawer(ev) {
      const { direction, delta, isFinal } = ev;

      this.drawerPos = Math.max(
        drawerMinHeight,
        Math.min(this.drawerMaxHeight, this.drawerPos - delta.y)
      );

      if (isFinal === true) {
        this.$nextTick(() => {
          const aboveHalf = this.drawerOpenRatio > drawerOpenRatioHalf;
          const targetHeight =
            direction === 'up'
              ? aboveHalf
                ? this.drawerMaxHeight
                : Math.round(this.drawerMaxHeight / 2)
              : aboveHalf
              ? Math.round(this.drawerMaxHeight / 2)
              : drawerMinHeight;

          this.animateDrawerTo(targetHeight);
        });
      }
    },

    cycleDrawer() {
      const targetHeight =
        this.drawerMode === 'handler'
          ? Math.round(this.drawerMaxHeight / 2)
          : this.drawerMode === 'half'
          ? this.drawerMaxHeight
          : drawerMinHeight;

      this.animateDrawerTo(targetHeight);
    },

    animateDrawerTo(height) {
      clearTimeout(this.animateTimeout);

      const diff = height - this.drawerPos;

      if (diff !== 0) {
        this.drawerPos += Math.abs(diff) < 2 ? diff : Math.round(diff / 2);

        this.animateTimeout = setTimeout(() => {
          this.animateDrawerTo(height);
        }, 30);
      }
    },
  },
};
</script>

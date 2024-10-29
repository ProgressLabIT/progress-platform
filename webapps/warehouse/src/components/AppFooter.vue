<template>
  <q-footer class="footer footer-text">
    <div>
      <q-card
        class="slide-drawer slide-drawer--bottom text-white fixed-bottom column no-wrap"
        :class="`slide-drawer--open-${drawerMode}`"
        :style="drawerStyle"
      >
        <q-card-section
          v-touch-pan.mouse.vertical="slideDrawer"
          class="slide-drawer__handler--horizontal row flex-center q-pa-sm q-gutter-x-md"
        >
          <div class="cursor-pointer" @click="cycleDrawer"></div>
        </q-card-section>

        <q-card-section v-if="drawerMode !== 'handler'" class="col">
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
    <div class="row q-pa-sm display smaller">
      <div class="col">{{ config.companyName }}</div>
      <div style="width: 90px">{{ time }}</div>
      <div class="col text-right">{{ date }}</div>
    </div>
  </q-footer>
</template>

<script>
import { DateTime } from 'luxon';
import { useConfigStore } from '../stores/config';

const drawerMinHeight = 50;
const drawerTopOffset = 100;
const drawerOpenRatioHalf = 50;

export default {
  name: 'AppFooter',

  setup() {
    const { config } = useConfigStore();
    return {
      config,
    };
  },

  data() {
    return {
      now: 0,
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
    time() {
      return this.now
        .setLocale(this.$i18n.locale)
        .toLocaleString(DateTime.TIME_WITH_SECONDS);
    },
    date() {
      return this.now
        .setLocale(this.$i18n.locale)
        .toLocaleString(DateTime.DATE_HUGE);
    },
  },

  created() {
    this.now = DateTime.local();
    setInterval(() => {
      this.now = DateTime.local();
    }, 1000);
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

<style lang="css" scoped>
.material-icons.smaller {
  font-size: 0.9em;
  vertical-align: bottom;
}

.footer-text {
  color: rgba(255, 255, 255, 0.6);
}

.slide-drawer--bottom {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  background-color: #333;
  background-image: radial-gradient(
    circle,
    rgba(0, 0, 0, 0.1) 0%,
    rgba(0, 0, 0, 0.4) 100%
  );
  bottom: unset;
  top: 100%;
  transition: background-color 0.3s ease-in-out;
}
.slide-drawer--bottom > div:last-child,
.slide-drawer--bottom > img:last-child {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}
.slide-drawer--bottom.slide-drawer--open-half {
  background-color: #014a88;
}
.slide-drawer--bottom.slide-drawer--open-full {
  background-color: #01884a;
}
.slide-drawer__handler--horizontal {
  cursor: grab;
}
.slide-drawer__handler--horizontal > div {
  width: 120px;
  height: 8px;
  border-radius: 4px;
  background-color: rgba(200, 200, 200, 0.7);
}
</style>

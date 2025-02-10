<template>
  <q-footer
    class="footer footer-text bg-blue-backdrop"
    style="min-height: 29px;"
    @click="
      (event) => {
        event.stopPropagation();
      }
    "
  >
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

        <!-- HANDLE PRINT LABEL -->
        <q-card-section
          v-if="drawerMode !== 'handler' && show_print_label"
          class="col"
        >
          <PrintLabelForm
            :product="product"
            :supplier="supplier"
            :containers="containers"
            :print_templates="print_templates"
            :available_height="available_height"
          />
        </q-card-section>

        <!-- HANDLE CREATE CONTAINER -->
        <q-card-section
          v-else-if="drawerMode !== 'handler' && show_create_container"
          class="col"
        >
          <CreateContainerForm :available_height="available_height" />
        </q-card-section>

        <!-- ROUTER PART -->
        <q-card-section v-if="drawerMode !== 'handler'" class="col">
          <q-tabs class="col-auto" vertical switch-indicator inline-label>
            <q-route-tab
              v-for="tab in Object.keys(tab_routes)"
              :key="tab"
              :to="{ name: tab }"
              active-class="text-theme-blue"
              indicator-color="theme-blue"
              content-class="display"
              :icon="tab_routes[tab]"
              :label="$t(`views.${tab}`)"
              @click="forceHide"
            />
          </q-tabs>
        </q-card-section>
      </q-card>
    </div>
  </q-footer>
</template>

<script>
import { DateTime } from 'luxon';
import CreateContainerForm from '@/components/CreateContainerForm.vue';
import PrintLabelForm from '@/components/print/PrintLabelForm.vue';
import { useConfigStore } from '../stores/config';

const drawerMinHeight = 30;
const drawerTopOffset = 100;
const drawerOpenRatioHalf = 50;

export default {
  name: 'AppFooter',

  components: { PrintLabelForm, CreateContainerForm },

  setup() {
    const { config } = useConfigStore();
    return {
      config,
    };
  },

  data() {
    return {
      tab_routes: {
        IncomingRoot: 'mdi-import',
        TransferRoot: 'mdi-swap-vertical',
        ShipmentRoot: 'mdi-export',
        InventoryRoot: 'mdi-warehouse',
      },
      show_print_label: false,
      show_create_container: false,
      print_templates: undefined,
      product: undefined,
      supplier: undefined,
      available_height: 0,
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

    hasSecondaryContent() {
      return this.show_print_label;
    },
  },

  created() {
    this.now = DateTime.local();
    setInterval(() => {
      this.now = DateTime.local();
    }, 1000);

    this.$bus.on('show-print-templates', (context) => {
      this.show_print_label = true;
      this.show_create_container = false;
      this.product = context.product;
      this.supplier = context.supplier;
      this.containers = context.containers;
      this.print_templates = context.print_templates;
      this.forceShow();
    });

    this.$bus.on('show-create-container', () => {
      this.show_create_container = true;
      this.show_print_label = false;
      this.forceShow();
    });

    this.$bus.on('close-footer', () => {
      this.forceHide();
    });
  },

  beforeUnmount() {
    clearTimeout(this.animateTimeout);
  },

  methods: {
    clean() {
      this.show_print_label = false;
      this.product = undefined;
      this.supplier = undefined;
      this.print_templates = undefined;

      this.show_create_container = false;
      this.containers = undefined;
    },

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
          : this.drawerMode === 'half' && this.hasSecondaryContent
          ? this.drawerMaxHeight
          : drawerMinHeight;

      this.animateDrawerTo(targetHeight);
    },

    forceShow() {
      this.animateDrawerTo(Math.round(this.drawerMaxHeight / 2));
    },

    forceHide() {
      this.drawerMode === 'handler';
      this.animateDrawerTo(drawerMinHeight);
    },

    animateDrawerTo(height) {
      if (height === drawerMinHeight) {
        this.clean();
      }
      clearTimeout(this.animateTimeout);

      const diff = height - this.drawerPos;

      if (diff !== 0) {
        this.drawerPos += Math.abs(diff) < 2 ? diff : Math.round(diff / 2);

        this.animateTimeout = setTimeout(() => {
          this.available_height = height;
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

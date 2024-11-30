<template>
  <div class="column q-px-md fit">
    <!-- HEADER -->
    <div class="row items-center">
      <div
        v-if="!(edit_mode && can_edit)"
        class="text-h4 col-auto text-uppercase"
      >
        {{ ' # ' + position?.code }}
      </div>
      <q-input
        v-else
        :model-value="position.code"
        dense
        filled
        :label="$t('warehouse.position.code')"
        class="input-uppercase"
        @update:model-value="(v) => (position.code = v.toUpperCase())"
      >
      </q-input>

      <q-space></q-space>
    </div>

    <!-- SUB HEADER -->
    <div class="row q-pt-md q-col-gutter-lg items-center text-h6">
      <div class="col-auto text-h5 text-low text-uppercase">
        {{ $t('creation_date') }}
      </div>
      <div class="col-auto">{{ position_created_time_string }}</div>
    </div>

    <!-- POSITION DATA -->
    <q-tabs
      v-model="tab"
      dense
      class="q-mt-md text-low"
      content-class="text-h5"
      indicator-color="theme-blue"
      align="left"
      active-class="text-high weight-bold"
    >
      <q-tab
        name="form"
        :label="$t('warehouse.position.position_data')"
        class="text-left"
      />
    </q-tabs>

    <q-card square class="col surface2 scroll">
      <q-tab-panels v-model="tab" class="transparent">
        <!-- POSITION FORM DATA
        <q-tab-panel name="form">
          <template v-if="serial.data.length > 0">
            <div class="column col scroll q-pt-sm">
              <FormField
                v-for="field in serial.data"
                :key="field._key"
                :field="field"
                :root-path="`/media/serial/${serial_key}/${field._key}`"
                :disable="!(edit_mode && can_edit)"
                @update="field.value = $event"
              />
            </div>
          </template>
          <div v-else class="col-auto text-italic">No data</div>
        </q-tab-panel> -->
      </q-tab-panels>
    </q-card>
  </div>
</template>

<script>
export default {
  name: 'PositionDetailForm',

  props: {
    // from router
    position_key: {
      type: String,
      required: true,
    },

    edit_mode: {
      type: Boolean,
      required: true,
    },
  },

  emits: ['exit'],

  data() {
    return {
      tab: 'form',
      loading: false,
      recording: false,
      data_column_width: 65,
    };
  },

  computed: {
    position() {
      return this.$store.getters.getPositionData(this.position_key);
    },

    position_created_time_string() {
      const config = {
        year: '2-digit',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      };
      return this.$capitalize(
        this.$formatDateTime(this.position?.created, this.$i18n.locale, config),
      );
    },
    can_edit() {
      return !this.$store.getters.getPositionData(this.position_key).deleted;
    },
  },

  methods: {
    getHumanDate(timestamp) {
      const config = {
        year: '2-digit',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit',
        weekday: 'short',
      };
      return this.$capitalize(
        this.$formatDateTime(timestamp, this.$i18n.locale, config),
      );
    },

    notify({ message, color = 'theme-green' }) {
      this.$q.notify({
        message,
        color,
        timeout: '1500',
        position: 'top',
      });
    },
  },
};
</script>

<style lang="sass" scoped>
.dot
  height: 13px
  width: 13px
  border-radius: 100%
  background-color: #888
  border: 5px solid var(--surface-2)
  box-sizing: content-box
  z-index:99

.thread
  position: absolute
  height: 100%
  left: 11px
  top: 20px
  width: 1px
  background-color: #fff3
</style>

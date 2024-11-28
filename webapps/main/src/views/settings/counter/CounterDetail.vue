<template>
  <div class="q-pa-lg column full-height">
    <q-form class="full-height column" @submit="save">
      <div class="row justify-between items-start">
        <div class="col-10 row q-col-gutter-md">
          <!-- Counter name -->
          <div class="col-4">
            <q-input
              v-model="temp_data.name"
              :rules="[(value) => !!value || $t('field_required_alert')]"
              filled
              :disable="!editMode"
              :label="$t('name')"
              stack-label
            />
          </div>

          <!-- Next Tick -->
          <div class="col-4">
            <q-input
              v-model="temp_data.next_tick"
              filled
              :label="$t('next_tick')"
              :disable="!editMode"
              stack-label
            />
          </div>

          <!-- Frequency -->
          <div class="col-4">
            <!--<q-input
              v-model="temp_data.frequency"
              filled
              :label="$t('frequency')"
              :disable="!editMode"
              stack-label
            />-->

            <!--<q-select
              v-model="temp_data.frequency"
              filled
              :rules="[(value) => !!value || $t('field_required_alert')]"
              :options="[$t('year'), $t('month'), $t('week')]"
              :label="$t('frequency')"
              class="q-mt-md"
              :disable="!editMode"
              @update:model-value="(selection) => calculateResetDate(selection)"
            />-->
            <q-select
              v-model="temp_data.frequency"
              filled
              :rules="[(value) => !!value || $t('field_required_alert')]"
              :options="[$t('none'), $t('year'), $t('month'), $t('week'), $t('day')]"
              :label="$t('reset_frequency')"
              class="q-mt-md"
              :disable="!editMode"
              @update:model-value="(selection) => refreshResetDate(selection)"
            />
          </div>

          <!-- reset date -->
          <div class="col-4">
            <q-input
              v-model="temp_data.reset_date"
              filled
              mask="date"
              :label="$t('reset_date')"
              disable
            >
              <template #append>
                <q-icon name="mdi-calendar" class="cursor-pointer">
                  <q-popup-proxy
                    cover
                    transition-show="scale"
                    transition-hide="scale"
                  >
                    <q-date v-model="temp_data.reset_date">
                      <div class="row items-center justify-end">
                        <q-btn
                          v-close-popup
                          label="Close"
                          color="primary"
                          flat
                        />
                      </div>
                    </q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>
          </div>

          <!-- Template -->
          <div class="col-8">
            <TemplateSelect v-model="template_model" :disable="!editMode" />
          </div>
        </div>

        <!-- ACTION BUTTONS -->
        <div class="col-auto">
          <template v-if="!editMode">
            <BaseTooltipIcon
              icon="mdi-pencil"
              :tooltip="$capitalize($t('edit'))"
              :color="$theme.blue"
              @icon-click="editMode = true"
            />

            <BaseTooltipIcon
              icon="mdi-delete"
              :tooltip="$capitalize($t('delete'))"
              :color="$theme.red"
              @icon-click="show_delete = true"
            />
          </template>

          <template v-else>
            <div class="col column q-gutter-md">
              <q-btn
                type="submit"
                size="12px"
                color="theme-blue"
                :loading="saving"
                :label="$t('save')"
              />

              <q-btn
                size="12px"
                color="theme-grey"
                :label="$t('cancel')"
                @click="cancel"
              />
            </div>
          </template>
        </div>
      </div>
    </q-form>

    <BaseDialog :show="show_delete" @close="show_delete = false">
      <BaseActionCard
        :title="$t('counter_delete')"
        :save-label="$t('confirm')"
        save-color="theme-red"
        @save="deleteCounter"
        @cancel="show_delete = false"
      >
        {{ $t('counter_delete_text') }}
      </BaseActionCard>
    </BaseDialog>
  </div>
</template>

<script>
import { date } from 'quasar';
import { ref } from 'vue';
import BaseActionCard from '@/components/BaseActionCard.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue';
import TemplateSelect from '@/components/settings/counters/TemplateSelect.vue';
import { calculateNextResetDate } from '@/lib/dateUtils';

export default {
  name: 'CounterDetail',

  components: {
    BaseActionCard,
    BaseDialog,
    BaseTooltipIcon,
    TemplateSelect,
  },

  props: {
    counter: {
      type: Object,
      required: true,
    },
  },

  emits: ['reload'],

  setup() {
    const template_model = ref(null);
    return {
      template_model,
    };
  },

  data() {
    return {
      temp_data: {
        name: null,
        next_tick: null,
        template: [],
        frequency: null,
        reset_date: null,
      },
      table_loading: false,
      saving: false,
      show_delete: false,
      editMode: false,
    };
  },

  computed: {
    search_disabled() {
      return this.editMode;
    },
  },

  watch: {
    counter: {
      handler() {
        this.initTempCounterData();
        this.editMode = false;
      },
    },
  },

  mounted() {
    this.initTempCounterData();
  },

  methods: {
    refreshResetDate(reset_period) {
      this.temp_data.reset_date = calculateNextResetDate({
        reset_period: this.getFrequency(reset_period),
      }).resetDate;
    },

    getFrequencyExt(reset_period) {
      return this.$t(reset_period);
    },

    getFrequency(reset_period) {
      switch (reset_period) {
        case this.$t('none'):
          return 'none';
        case this.$t('day'):
          return 'day';
        case this.$t('week'):
          return 'week';
        case this.$t('month'):
          return 'month';
        case this.$t('year'):
          return 'year';
        default:
          return undefined;
      }
    },

    initTempCounterData() {
      if (this.counter) {
        Object.keys(this.temp_data).forEach(
          (k) => (this.temp_data[k] = this.counter[k]),
        );
        this.temp_data.frequency = this.getFrequencyExt(this.counter.frequency);
        this.refreshResetDate(this.temp_data.frequency);
        this.template_model = this.counter.template;
      }
    },

    save() {
      this.saving = true;
      const data = {
        name: this.temp_data.name,
        frequency: this.getFrequency(this.temp_data.frequency),
        template: this.template_model,
        next_tick: this.temp_data.next_tick,
        reset_date: date.formatDate(
          calculateNextResetDate({
            reset_period: this.getFrequency(this.temp_data.frequency),
          }).resetDate,
          'YYYY-MM-DDTHH:mm:ss.SSSZ',
        ),
      };
      const calls = [
        this.$api.put(`counter/${this.counter._key}`, {
          ...this.counter,
          ...data,
        }),
      ];

      Promise.all(calls).then(() => {
        this.$emit('reload');
        this.saving = false;
        this.editMode = false;
      });
    },

    cancel() {
      this.initTempCounterData();
      this.editMode = false;
      this.saving = false;
    },

    deleteCounter() {
      this.$api.delete(`counter/${this.counter._key}`).then(() => {
        this.$q.notify({
          message: this.$t('counter_delete_success'),
          color: 'theme-green',
          timeout: 1500,
          position: 'top',
        });
        this.$emit('reload');
        this.$router.push({ name: 'counterLibrary' });
      });
    },
  },
};
</script>

<style lang="sass">
#list-values thead
  position: sticky
  z-index: 1
  top: 0

  tr:first-child th /* bg color is important for th; just specify one */
    background-color: var(--surface-2)
    padding-top: 8px
    padding-bottom: 8px
    border-bottom: 1px solid rgba(255, 255, 255, .3)

.table-no-hover
  td::before
    // remove hover highlight
    background-color: transparent
</style>

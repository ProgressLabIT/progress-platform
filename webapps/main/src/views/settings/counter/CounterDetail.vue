<template>
  <div class="q-pa-lg column full-height">
    <q-form class="full-height column" @submit="save">
      <div class="row justify-between items-start">
        <div class="col-10 row q-col-gutter-md">
          <!-- Counter name -->
          <div class="col-4">
            <q-input
              v-model="temp_data.name"
              :rules="[(value) => !!value || $t('counter_required_alert')]"
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
            <q-input
              v-model="temp_data.frequency"
              filled
              :label="$t('frequency')"
              :disable="!editMode"
              stack-label
            />
          </div>

          <!-- reset date -->
          <div class="col-4">
            <q-input
              v-model="temp_data.reset_date"
              filled
              mask="date"
              :label="$t('reset_date')"
              :rules="['date']"
              :disable="!editMode"
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
            <q-select
              v-model="template_model"
              filled
              :label="$t('template')"
              use-input
              use-chips
              multiple
              input-debounce="0"
              :options="filterOptions"
              :disable="!editMode"
              @new-value="createValue"
              @filter="filterFn"
            />
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

    <BaseDialog :show="show_delete">
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

const templateOptions = ['%y', '%m', '%d', '/', '#2', '#3', '#4', '#5', '#6'];

export default {
  name: 'CounterDetail',

  components: {
    BaseActionCard,
    BaseDialog,
    BaseTooltipIcon,
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
    const filterOptions = ref(templateOptions);

    return {
      template_model,
      filterOptions,

      createValue(val, done) {
        // Calling done(var) when new-value-mode is not set or is "add", or done(var, "add") adds "var" content to the model
        // and it resets the input textbox to empty string
        // ----
        // Calling done(var) when new-value-mode is "add-unique", or done(var, "add-unique") adds "var" content to the model
        // only if is not already set and it resets the input textbox to empty string
        // ----
        // Calling done(var) when new-value-mode is "toggle", or done(var, "toggle") toggles the model with "var" content
        // (adds to model if not already in the model, removes from model if already has it)
        // and it resets the input textbox to empty string
        // ----
        // If "var" content is undefined/null, then it doesn't tampers with the model
        // and only resets the input textbox to empty string

        if (val.length > 0) {
          const modelValue = (template_model.value || []).slice();

          val
            .split(/[,;|]+/)
            .map((v) => v.trim())
            .filter((v) => v.length > 0)
            .forEach((v) => {
              if (templateOptions.includes(v) === false) {
                templateOptions.push(v);
              }
              if (modelValue.includes(v) === false) {
                modelValue.push(v);
              }
            });

          done(null);
          template_model.value = modelValue;
        }
      },

      filterFn(val, update) {
        update(() => {
          if (val === '') {
            filterOptions.value = templateOptions;
          } else {
            const needle = val.toLowerCase();
            filterOptions.value = templateOptions.filter(
              (v) => v.toLowerCase().indexOf(needle) > -1,
            );
          }
        });
      },
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
    initTempCounterData() {
      if (this.counter) {
        Object.keys(this.temp_data).forEach(
          (k) => (this.temp_data[k] = this.counter[k]),
        );
        this.template_model = this.counter.template;
      }
    },

    save() {
      this.saving = true;
      const data = {
        name: this.temp_data.name,
        frequency: this.temp_data.frequency,
        template: this.template_model,
        next_tick: this.temp_data.next_tick,
        reset_date: date.formatDate(
          this.temp_data.reset_date,
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

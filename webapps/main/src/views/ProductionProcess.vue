<template>
  <div class="row full-height q-py-md">
    <!-- ASIDE - PHASE LIST -->
    <div class="col-3 column full-height" style="min-width: 400px">
      <div class="q-px-lg">
        <div class="text-h1 display highlight">
          {{ product_data.code }}
        </div>
        <div class="text-body1">
          {{ product_data.description }}
        </div>

        <div class="text-h5 q-mt-lg q-mb-sm text-uppercase">
          {{ $t('phase.long', 2) }}
        </div>
      </div>

      <q-separator inset />

      <div class="scroll col q-py-sm full-width">
        <q-list
          id="phases"
          dense
          class="transparent medium text-left q-pl-sm"
          align="left"
        >
          <q-item
            v-for="(phase, index) in process"
            :key="phase._key"
            v-ripple
            clickable
            :name="index"
            :class="`full-width text-left ${editMode ? '' : 'undraggable'}`"
            @mouseenter="dragging ? undefined : (over_phase = index)"
            @mouseleave="dragging ? undefined : (over_phase = null)"
            @click="goToPhase(index)"
          >
            <q-item-section avatar class="col-auto">
              <q-avatar
                size="20px"
                :color="current_phase === index ? 'theme-blue' : 'theme-grey'"
                class="display smaller"
                :class="{ highlight: current_phase === index }"
              >
                {{ index + 1 }}
              </q-avatar>
            </q-item-section>

            <q-item-section>
              <q-item-label
                class="display ellipsis"
                :class="
                  current_phase === index
                    ? 'highlight'
                    : 'text-low weight-medium'
                "
              >
                {{ phase.alias }}
              </q-item-label>
            </q-item-section>

            <q-item-section v-if="editMode" v-show="over_phase === index" side>
              <div class="row items-center">
                <BaseTooltipIcon
                  icon="mdi-pencil"
                  :tooltip="$t('rename')"
                  :color="$theme.blue"
                  @icon-click="update_alias_at_index = index"
                />
                <BaseTooltipIcon
                  icon="mdi-delete"
                  :tooltip="$t('delete')"
                  :color="$theme.red"
                  @icon-click="confirming_delete = index"
                />
              </div>
            </q-item-section>
          </q-item>

          <!-- PHASE ALIAS UPDATE PROMPT -->
          <BasePrompt
            :show="update_alias_at_index !== null"
            :initial_value="
              update_alias_at_index
                ? process[update_alias_at_index].alias
                : null
            "
            :prompt="$t('phase.rename')"
            @update="updatePhaseAlias"
            @close="update_alias_at_index = null"
          />
        </q-list>
      </div>

      <q-space />

      <q-separator inset />

      <!-- ACTION BUTTONS -->
      <div class="column q-gutter-y-sm q-px-lg q-mt-sm q-pb-sm col-auto">
        <template v-if="!editMode">
          <q-btn
            class="full-width"
            color="theme-orange"
            icon="mdi-content-copy"
            :label="$t('copy')"
            @click="openMassCopyDialog"
          />

          <q-btn
            class="full-width"
            color="theme-blue"
            :label="$t('edit')"
            @click="toggleEdit"
          />
        </template>
        <template v-else>
          <BaseAutocompleteOperation
            dense
            :label="$capitalize($t('phase.add'))"
            :clearable="false"
            @select="addPhase"
          />
          <q-btn
            class="full-width q-mt-md"
            color="theme-green"
            :loading="saving"
            @click="saveChanges"
          >
            {{ $t('save') }}
          </q-btn>
          <q-btn class="full-width" color="theme-grey" @click="cancelChanges">
            {{ $t('cancel') }}
          </q-btn>
        </template>
      </div>
    </div>

    <!-- PHASE DETAILS -->
    <div class="col q-pr-md">
      <q-tabs
        v-model="activeTab"
        class="transparent text-low display"
        active-class="highlight"
        align="right"
        shrink
        dense
        indicator-color="theme-blue"
      >
        <q-tab name="steps">
          {{ $t('views.PhaseSteps') }}
        </q-tab>

        <q-tab name="parameters">
          {{ $t('views.PhaseParameters') }}
        </q-tab>

        <q-tab name="notes">
          {{ $t('views.PhaseNotes') }}
        </q-tab>

        <!-- TODO: Enable after templates are being utilized somewhere -->
        <q-tab v-if="false" name="print_templates">
          {{ $t('views.PhasePrintTemplates') }}
        </q-tab>
      </q-tabs>
      <q-card square class="scroll" :style="`height: ${card_height}px`">
        <q-tab-panels
          v-if="process[current_phase]"
          v-model="activeTab"
          keep-alive
          class="fit surface2"
        >
          <q-tab-panel name="steps">
            <ProcessSteps
              v-model="process[current_phase].steps"
              :edit-mode="editMode"
            />
          </q-tab-panel>

          <q-tab-panel name="parameters">
            <ProcessParameters
              v-model="process[current_phase].params"
              :process-has-steps="process[current_phase].steps.length > 0"
              :edit-mode="editMode"
            />
          </q-tab-panel>

          <q-tab-panel name="notes">
            <ProductionNotes
              v-model="process[current_phase].production_notes"
              :edit-mode="editMode"
            />
          </q-tab-panel>

          <q-tab-panel name="print_templates">
            <PhasePrintTemplates
              v-model="process[current_phase].print_templates"
              :edit-mode="editMode"
            />
          </q-tab-panel>
        </q-tab-panels>
      </q-card>
    </div>
  </div>
</template>

<script>
import { Dialog, Notify, uid } from 'quasar';
import Sortable from 'sortablejs';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { mapActions, useStore } from 'vuex';
import { api } from '@/boot/axios';
import BaseAutocompleteOperation from '@/components/BaseAutocompleteOperation.vue';
import BasePrompt from '@/components/BasePrompt.vue';
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue';
import MassCopyProcessDialog from '@/components/MassCopyProcessDialog.vue';
import PhasePrintTemplates from '@/components/PhasePrintTemplates.vue';
import ProcessParameters from '@/components/ProcessParameters.vue';
import ProductionNotes from '@/components/ProductionNotes.vue';
import ProcessSteps from '@/components/process-steps/ProcessSteps.vue';
// import PhaseAssignments from '@/components/PhaseAssignments.vue'

export default {
  name: 'ProductionProcess',

  components: {
    ProcessParameters,
    ProcessSteps,
    ProductionNotes,
    PhasePrintTemplates,
    // PhaseAssignments,
    BasePrompt,
    BaseTooltipIcon,
    BaseAutocompleteOperation,
  },

  emits: ['changesSaved', 'changesCanceled'],

  setup() {
    const { t } = useI18n();
    const store = useStore();
    const route = useRoute();

    function openMassCopyDialog() {
      const sourceProduct = store.getters.productData(route.params.product_key);
      Dialog.create({
        component: MassCopyProcessDialog,
        componentProps: {
          sourceProduct,
        },
      }).onOk(async (selectedProducts) => {
        // TODO: Add error handling
        await api.post(`/product/${sourceProduct._key}/process/copy`, {
          target_product_keys: selectedProducts.map(({ _key }) => _key),
        });
        Notify.create({
          type: 'positive',
          message: t('massCopyProcess.success.product', {
            count: selectedProducts.length,
          }),
        });
      });
    }

    return {
      openMassCopyDialog,
    };
  },

  data() {
    return {
      activeTab: 'steps',
      new_op: null,
      over_phase: null,
      confirming_delete: null,
      update_alias_at_index: null,
      saving: false,
      dragging: false,
    };
  },

  computed: {
    card_height() {
      return this.$q.screen.height - 114;
    },

    product_key() {
      return this.$route.params.product_key;
    },

    product_data() {
      return this.$store.getters.productData(this.product_key);
    },

    editMode: {
      get() {
        return this.$store.state.product.edit_modes.process;
      },
      set(value) {
        this.$store.commit('TOGGLE_EDIT_MODE', { view: 'process', value });
      },
    },

    current_phase: {
      get() {
        return this.product_data.last_phase;
      },

      set(value) {
        this.$store.commit('UPDATE_PRODUCT_NAV_STATE', {
          _key: this.product_key,
          last_phase: value,
        });
      },
    },

    process: {
      get() {
        return this.$store.state.process.temp;
      },

      set(value) {
        this.$store.commit('UPDATE_PROCESS', value);
      },
    },
  },

  watch: {
    confirming_delete() {
      const index = this.confirming_delete;
      if (index != null) {
        const phase = this.process[index];
        this.$q
          .dialog({
            title: phase.alias,
            cancel: true,
            // TODO: i18n
            message: `Confermi di voler eliminare questa fase?`,
          })
          .onOk(() => {
            this.deletePhase(index);
          })
          .onDismiss(() => {
            this.confirming_delete = null;
          });
      }
    },
  },

  mounted() {
    // Create step map
    const step_map = Array(this.process.length).fill(0);
    this.updateStepsMap(step_map);

    // Initialize draggable phases
    const container = document.querySelector('#phases');
    const _self = this;
    Sortable.create(container, {
      ..._self.$store.state.drag_options,
      filter: '.undraggable',
      onStart: () => {
        _self.dragging = true;
      },
      // use onEnd event provided by SortableJs library
      onEnd: ({ newIndex, oldIndex }) => {
        _self.dragging = false;
        const moved = _self.process.splice(oldIndex, 1)[0];
        _self.process.splice(newIndex, 0, moved);
        _self.updateActivePhaseIndex({ oldIndex, newIndex });
      },
    });
  },

  methods: {
    ...mapActions(['loadProductDetails']),

    toggleEdit() {
      this.editMode = true;
    },

    goToPhase(index) {
      this.confirming_delete = null;
      this.current_phase = index;
    },

    cancelChanges() {
      const active_phase = this.process[this.current_phase];
      if (active_phase) {
        const original_process = this.$store.state.process.saved;
        const original_phase_index = original_process.findIndex(
          (p) => p._key === active_phase._key,
        );
        this.updateActivePhaseIndex({
          oldIndex: this.current_phase,
          // If we canceled a newly created phase, set it to the first one
          newIndex: original_phase_index === -1 ? 0 : original_phase_index,
        });
      }

      this.$store.commit('CANCEL_PROCESS_CHANGES');
      this.confirming_delete = null;
      this.editMode = false;
      this.$emit('changesCanceled');
    },

    async addPhase(new_operation) {
      // Load media from default steps as temp files so that they can be uploaded as fresh
      // TODO: Migrate process to new media structure so that this is not needed and we don't end up with duplicate files
      const steps = await Promise.all(
        new_operation.default_phase_steps?.map(async (step) => ({
          ...step,
          media: await Promise.all(
            step.media?.map(async (media) => {
              const { data: blob } = await api.get(`/media/${media._key}`, {
                responseType: 'blob',
              });

              return {
                ...media,
                temp: true,
                data: new File([blob], media.filename, { type: blob.type }),
              };
            }) ?? [],
          ),
          print_templates:
            step.print_templates?.map((template) => ({
              ...template,
              temp: true,
            })) ?? [],
          // Copy the steps over with a different _key to "break the link"
          form_fields: step.form_fields.map((field) => ({
            ...field,
            _key: uid(),
          })),
        })) ?? [],
      );

      this.process.push({
        // Add temp _key so that sorting works with new phases too
        _key: Date.now(),
        alias: new_operation.name,
        operation_key: new_operation._key,
        product_key: this.product_key,
        params: new_operation.default_phase_parameters,
        production_notes: new_operation.default_phase_notes,
        steps,
        print_templates: [],
      });
      this.current_phase = this.process.length - 1;
    },

    deletePhase(phase_index) {
      this.$store.commit('DELETE_PHASE', phase_index);
      this.current_phase = this.process.length - 1;
      this.confirming_delete = null;
    },

    updateStepsMap(map) {
      this.$store.commit('UPDATE_PRODUCT_NAV_STATE', {
        _key: this.product_key,
        last_steps: map,
      });
    },

    updateActivePhaseIndex({ oldIndex, newIndex }) {
      // Moved active phase
      if (this.current_phase === oldIndex) {
        this.current_phase = newIndex;
      }
      // Moved earlier phase after active one
      else if (
        oldIndex < this.current_phase &&
        newIndex >= this.current_phase
      ) {
        this.current_phase--;
      }
      // Moved later phase before active one
      else if (
        oldIndex > this.current_phase &&
        newIndex <= this.current_phase
      ) {
        this.current_phase++;
      }

      // ADD HERE REORDERING OF last_steps MAP
      const new_steps_map = [...this.product_data.last_steps];
      const moved = new_steps_map.splice(oldIndex, 1)[0];
      new_steps_map.splice(newIndex, 0, moved);

      this.updateStepsMap(new_steps_map);
    },

    updatePhaseAlias(value) {
      this.process[this.update_alias_at_index].alias = value.toUpperCase();
      this.update_alias_at_index = null;
    },

    saveChanges() {
      this.saving = true;
      const process_update = {
        product_key: this.product_key,
        new_process: this.process.map((p) => {
          // remove temp _key
          if (typeof p._key == 'number') {
            delete p._key;
          }
          return p;
        }),
      };
      this.$store
        .dispatch('saveTempProcess', process_update)
        .then(() => {
          // Show progress long enough the let user notice something is going on
          // even if the update is instantaneous
          setTimeout(() => {
            this.confirming_delete = null;
            this.saving = false;
            this.editMode = false;
            this.$emit('changesSaved');
          }, 500);
        })
        .catch((error) => {
          window.alert(error);
          console.error(error);
          this.saving = false;
        });
    },
  },
};
</script>

<style lang="sass" scoped>
#phases .q-tab__content
  justify-content: left
</style>

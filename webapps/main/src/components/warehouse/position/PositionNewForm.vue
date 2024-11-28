<template>
  <BaseModalForm
    id="new-position-form"
    :loading="loading"
    max-width="80vw"
    @submit="postNewPosition"
    @cancel="$router.back()"
  >
    <template #title>
      {{ $t('warehouse.position.new') }}
    </template>

    <template #form>
      <!-- NEW POSITION FIELD LABELS -->
      <div class="row q-col-gutter-md">
        <div
          v-for="(info, field_name) in new_position_data"
          :key="field_name"
          :class="info.cols"
          class="text-h5 text-uppercase text-low"
        >
          {{ $capitalize(info.label) }}
        </div>
      </div>

      <!-- NEW POSITION DATA  -->
      <div
        v-for="(line, index) in new_positions"
        :key="index"
        class="row q-col-gutter-md q-py-sm items-center"
      >
        <div
          v-for="(info, field_name) in new_position_data"
          :key="field_name"
          :class="info.cols"
        >
          <q-input
            v-if="['start_from', 'due_by'].includes(field_name)"
            v-model="new_positions[index][field_name]"
            dense
            filled
            mask="####-##-##"
            hide-bottom-space
            :rules="[checkDate]"
          >
            <template #append>
              <q-icon name="mdi-calendar" class="cursor-pointer">
                <q-popup-proxy
                  cover
                  transition-show="scale"
                  transition-hide="scale"
                >
                  <q-date
                    v-model="new_positions[index][field_name]"
                    minimal
                    mask="YYYY-MM-DD"
                  >
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Close" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>

          <!--<BaseAutocompleteProduct
            v-else-if="field_name === 'product'"
            dense
            :load-data="false"
            :value="new_positions[index].product"
            @select="new_positions[index].product = $event"
          >
          </BaseAutocompleteProduct>-->

          <q-input
            v-else
            v-model="new_positions[index][field_name]"
            dense
            filled
            autocomplete="false"
            :type="field_name === 'qt_planned' ? 'number' : ''"
          >
          </q-input>
        </div>

        <div class="col-auto">
          <BaseTooltipIcon
            v-if="new_positions.length > 1"
            icon="mdi-close"
            :tooltip="$t('delete')"
            :color="$theme.red"
            @icon-click="deleteRow(index)"
          >
          </BaseTooltipIcon>
        </div>
      </div>

      <q-btn flat class="display medium" @click="addLine">
        + {{ $t('warehouse.position.add') }}
      </q-btn>
    </template>
  </BaseModalForm>
</template>

<script>
import BaseModalForm from '@/components/BaseModalForm.vue';
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue';

export default {
  name: 'PositionNewForm',

  components: {
    BaseModalForm,
    BaseTooltipIcon,
  },

  data() {
    return {
      wo_code: null,
      new_positions: [],
      show_picker: -1,
      loading: false,
    };
  },

  computed: {
    new_position_data() {
      return {
        code: {
          label: this.$t('warehouse.position.code'),
          type: String,
          cols: 'col-2',
          initial_value: '',
        },
        parent: {
          label: this.$t('warehouse.position.parent_position'),
          type: Object,
          cols: 'col-3',
          initial_value: null,
        },
        owned: {
          label: this.$t('warehouse.position.owned'),
          type: Boolean,
          cols: 'col-1',
          initial_value: true,
        },
        available: {
          label: this.$t('warehouse.position.available'),
          type: Boolean,
          cols: 'col-1',
          initial_value: true,
        },
        disposable: {
          label: this.$t('warehouse.position.disposable'),
          type: Boolean,
          cols: 'col-1',
          initial_value: false,
        },
      };
    },
  },

  created() {
    this.addLine();
  },

  methods: {
    addLine() {
      let empty_line = Object.fromEntries(
        Object.entries(this.new_position_data).map(([field, value]) => [
          field,
          value.initial_value,
        ]),
      );
      this.new_positions.push(empty_line);
    },

    postNewPosition() {
      let new_records = this.new_positions.map((position) => {
        return {
          code: position.code.toUpperCase(),
          parent: position.parent,
          owned: position.owned,
          available: position.available,
          disposable: position.disposable,
        };
      });
      this.loading = true;
      this.$store
        .dispatch('postPositions', new_records)
        .then(() => {
          this.loading = false;
          this.$router.back();
        })
        .catch((err) => {
          window.alert(err);
          this.loading = false;
        });
    },

    deleteRow(index) {
      this.new_positions.splice(index, 1);
    },
  },
};
</script>

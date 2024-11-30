<template>
  <BaseModalForm
    id="new-position-form"
    :loading="loading"
    max-width="80vw"
    @submit="postNewPosition"
    @cancel="$emit('closePosition')"
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
          <q-toggle
            v-if="
              field_name === 'owned' ||
              field_name === 'available' ||
              field_name === 'disposable'
            "
            :model-value="new_positions[index][field_name]"
            :disable="false"
            @update:model-value="
              (value) => (new_positions[index][field_name] = value)
            "
          />

          <BaseAutocompletePosition
            v-else-if="field_name === 'parent'"
            dense
            :load-data="false"
            :value="new_positions[index].parent"
            @select="new_positions[index].parent = $event._key"
          >
          </BaseAutocompletePosition>

          <q-input
            v-else
            v-model="new_positions[index][field_name]"
            dense
            filled
            autocomplete="false"
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
import BaseAutocompletePosition from '@/components/warehouse/position/BaseAutocompletePosition.vue';

export default {
  name: 'PositionNewForm',

  components: {
    BaseModalForm,
    BaseTooltipIcon,
    BaseAutocompletePosition,
  },

  emits: ['closePosition'],

  data() {
    return {
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
          cols: 'col-4',
          initial_value: null,
        },
        owned: {
          label: this.$t('warehouse.position.owned'),
          type: Boolean,
          cols: 'col-2',
          initial_value: true,
        },
        available: {
          label: this.$t('warehouse.position.available'),
          type: Boolean,
          cols: 'col-2',
          initial_value: true,
        },
        disposable: {
          label: this.$t('warehouse.position.disposable'),
          type: Boolean,
          cols: 'col-2',
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
          parent_position_key: position.parent || 'IN',
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
          this.$emit('closePosition');
        })
        .catch((err) => {
          window.alert(err);
          this.loading = false;
          this.$emit('closePosition');
        });
    },

    deleteRow(index) {
      this.new_positions.splice(index, 1);
    },
  },
};
</script>

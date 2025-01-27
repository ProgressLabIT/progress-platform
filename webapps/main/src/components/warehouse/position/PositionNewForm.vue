<template>
  <BaseModalForm
    id="new-position-form"
    :loading="loading"
    max-width="90vw"
    @submit="postNewPosition"
    @cancel="$router.back()"
  >
    <template #title>
      {{ $t('warehouse.position.new') }}
    </template>

    <template #form>
      <!-- NEW POSITION DATA  -->
      <div
        v-for="(line, index) in new_positions"
        :key="index"
        class="row q-col-gutter-x-md q-py-sm items-start"
      >
          <div class="col">
            <q-input
              v-model="new_positions[index].code"
              filled
              :label="$t('code')"
              autocomplete="false"
            />
          </div>
          <div class="col">
            <BaseAutocompletePosition
              :load-data="false"
              :label="$t('warehouse.position.parent_position')"
              :value="new_positions[index]?.parent"
              @select="new_positions[index].parent = $event"
            />
          </div>

          <div
            class="col-auto q-gutter-sm"
            :key="field_name"
            v-for="field_name in ['owned', 'available', 'disposable', 'fixed']"
          >
            <q-checkbox
              :model-value="new_positions[index][field_name]"
              :disable="false"
              :label="$t(`warehouse.position.${field_name}`)"
              @update:model-value="
                (value) => (new_positions[index][field_name] = value)
              "
            />
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
          cols: 'col-4',
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
          cols: 'col-auto',
          initial_value: true,
        },
        available: {
          label: this.$t('warehouse.position.available'),
          type: Boolean,
          cols: 'col-auto',
          initial_value: true,
        },
        disposable: {
          label: this.$t('warehouse.position.disposable'),
          type: Boolean,
          cols: 'col-auto',
          initial_value: false,
        },
        fixed: {
          label: this.$t('warehouse.position.fixed'),
          type: Boolean,
          cols: 'col-auto',
          initial_value: false,
        },
      };
    },
  },

  created() {
    this.clear();
  },

  methods: {
    clear() {
      this.new_positions = [];
      this.show_picker = -1;
      this.addLine();
    },

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
          parent_position_key: position.parent?._key || 'IN',
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
          this.clear();
          this.$router.back();
        })
        .catch((err) => {
          window.alert(err);
          this.loading = false;
          this.clear();
          this.$router.back();
        });
    },

    deleteRow(index) {
      this.new_positions.splice(index, 1);
    },
  },
};
</script>

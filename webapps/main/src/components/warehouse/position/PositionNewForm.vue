<template>
  <BaseModalForm
    id="new-work-order-form"
    :loading="loading"
    max-width="80vw"
    @submit="postNewWorkOrder"
    @cancel="$router.back()"
  >
    <template #title>
      {{ $t('work_order.new') }}
    </template>

    <template #form>
      <!-- NEW WORK ORDER FIELD LABELS -->
      <div class="row q-col-gutter-md">
        <div
          v-for="(info, field_name) in new_wo_data"
          :key="field_name"
          :class="info.cols"
          class="text-h5 text-uppercase text-low"
        >
          {{ $capitalize(info.label) }}
        </div>
      </div>

      <!-- NEW WORK ORDER DATA  -->
      <div
        v-for="(line, index) in new_work_orders"
        :key="index"
        class="row q-col-gutter-md q-py-sm items-center"
      >
        <div
          v-for="(info, field_name) in new_wo_data"
          :key="field_name"
          :class="info.cols"
        >
          <q-input
            v-if="['start_from', 'due_by'].includes(field_name)"
            v-model="new_work_orders[index][field_name]"
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
                    v-model="new_work_orders[index][field_name]"
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

          <BaseAutocompleteProduct
            v-else-if="field_name === 'product'"
            dense
            :load-data="false"
            :value="new_work_orders[index].product"
            @select="new_work_orders[index].product = $event"
          >
          </BaseAutocompleteProduct>

          <q-input
            v-else
            v-model="new_work_orders[index][field_name]"
            dense
            filled
            autocomplete="false"
            :type="field_name === 'qt_planned' ? 'number' : ''"
          >
          </q-input>
        </div>

        <div class="col-auto">
          <BaseTooltipIcon
            v-if="new_work_orders.length > 1"
            icon="mdi-close"
            :tooltip="$t('delete')"
            :color="$theme.red"
            @icon-click="deleteRow(index)"
          >
          </BaseTooltipIcon>
        </div>
      </div>

      <q-btn flat class="display medium" @click="addLine">
        + {{ $t('work_order.add') }}
      </q-btn>
    </template>
  </BaseModalForm>
</template>

<script>
import { date } from 'quasar';
import BaseAutocompleteProduct from '@/components/BaseAutocompleteProduct.vue';
import BaseModalForm from '@/components/BaseModalForm.vue';
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue';

export default {
  name: 'PositionNewForm',

  components: {
    BaseAutocompleteProduct,
    BaseModalForm,
    BaseTooltipIcon,
  },

  data() {
    return {
      wo_code: null,
      new_work_orders: [],
      show_picker: -1,
      loading: false,
    };
  },

  computed: {
    default_due_by() {
      const now = new Date();
      return date.formatDate(now, 'yyyy/MM/dd');
    },

    new_wo_data() {
      return {
        code: {
          label: this.$t('work_order.wo_code'),
          type: String,
          cols: 'col-2',
          initial_value: '',
        },
        project_code: {
          label: this.$t('project'),
          type: String,
          cols: 'col-2',
          initial_value: '',
        },
        product: {
          label: this.$t('product.label'),
          type: Object,
          cols: 'col-3',
          initial_value: null,
        },
        qt_planned: {
          label: this.$t('quantity.long'),
          type: Number,
          cols: 'col-1',
          initial_value: 0,
        },
        start_from: {
          label: this.$t('work_order.list_headers.start_from'),
          type: Date,
          cols: 'col',
          initial_value: date.formatDate(new Date()),
        },
        due_by: {
          label: this.$t('by'),
          type: Date,
          cols: 'col',
          initial_value: date.formatDate(new Date()),
        },
      };
    },

    product_list() {
      return this.vuex_ready ? this.$store.getters.productCatalog() : [];
    },
  },

  created() {
    this.$store.dispatch('loadProductList');
    this.addLine();
  },

  methods: {
    addLine() {
      let empty_line = Object.fromEntries(
        Object.entries(this.new_wo_data).map(([field, value]) => [
          field,
          value.initial_value,
        ]),
      );
      this.new_work_orders.push(empty_line);
    },

    checkDate(d) {
      return date.isValid(d);
    },

    postNewWorkOrder() {
      const quantity_missing = this.new_work_orders.some(
        (wo) => wo.qt_planned == 0,
      );
      const product_missing = this.new_work_orders.some(
        (wo) => !wo.product._key,
      );

      if (quantity_missing || product_missing) {
        window.alert(this.$capitalize(this.$t('form_missing_fields_alert')));
      } else {
        let new_records = this.new_work_orders.map((wo) => {
          return {
            wo_code: wo.code.toUpperCase(),
            product_key: wo.product._key,
            product_code: wo.product.code,
            product_description: wo.product.description,
            qt_planned: wo.qt_planned,
            start_from: wo.start_from,
            due_by: wo.due_by,
            project_code: wo.project_code.toUpperCase(),
          };
        });
        this.loading = true;
        this.$store
          .dispatch('postWorkOrder', new_records)
          .then(() => {
            this.loading = false;
            this.$router.back();
          })
          .catch((err) => {
            window.alert(err);
            this.loading = false;
          });
      }
    },

    setDueBy(date, index) {
      this.$set(this.new_work_orders[index], 'due_by', date);
      this.show_picker = -1;
    },

    deleteRow(index) {
      this.new_work_orders.splice(index, 1);
    },
  },
};
</script>

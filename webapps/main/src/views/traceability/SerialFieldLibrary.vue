<template>
  <LoadingSignal v-if="!data_ready" />

  <div v-else class="row full-height">
    <div class="full-height column col-3">
      <q-input
        v-model="search_text"
        dense
        filled
        class="q-px-md q-pt-md"
        :placeholder="$capitalize($t('search'))"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>

      <div
        class="row q-mt-md q-px-lg q-py-sm text-h6 text-uppercase weight-bold"
      >
        <div class="col-3">
          {{ $t('type') }}
        </div>
        <div class="col">
          {{ $t('name') }}
        </div>
      </div>

      <q-separator />

      <!-- FIELD LIST -->
      <div class="scroll col">
        <div
          v-for="(field, index) in filtered_fields"
          :key="field._key"
          class="row pointer q-px-lg q-py-xs medium full-width"
          :class="{
            'alternate-row': index % 2 === 0,
            'bg-blue-backdrop': field._key === selected_field_key,
          }"
          style="white-space: nowrap"
          @click="showFieldDetail(field._key)"
        >
          <div class="col-3">
            <q-icon :name="getFieldIcon(field.type)" />
          </div>
          <div class="col">
            {{ $capitalize(field.name) }}
          </div>
        </div>
      </div>

      <q-separator />

      <!-- FIELD LIST COUNT -->
      <div class="row flex-center smaller q-py-xs">
        {{ filtered_fields.length }} {{ $t('of') }} {{ field_list.length }}
      </div>

      <div class="row item-center q-mb-xl">
        <q-btn
          color="theme-blue"
          class="q-ml-auto"
          size="12px"
          :label="$t('add_field')"
          @click="show_new_field_form = true"
        >
        </q-btn>
        <q-btn
          color="theme-red"
          class="q-ml-md"
          size="12px"
          :label="$t('remove_field')"
          :disable="!selected_field_key"
          @click="show_delete = true"
        >
        </q-btn>
      </div>
    </div>

    <BaseDialog :show="show_new_field_form" :no-backdrop-dismiss="false">
      <FormFieldSearch @close="show_new_field_form = false" @select="addField">
      </FormFieldSearch>
    </BaseDialog>

    <BaseDialog :show="show_delete" :no-backdrop-dismiss="false">
      <BaseActionCard
        :title="$t('field_delete')"
        :save-label="$t('confirm')"
        save-color="theme-red"
        @save="deleteField"
        @cancel="show_delete = false"
      >
        {{ $t('serial_field_delete_text') }}
      </BaseActionCard>
    </BaseDialog>
    <!-- FIELD DATA -->

    <!--q-separator vertical />


    <div v-if="data_ready" class="col full-height">
      <router-view :field="selected_field" @reload="getFields"> </router-view>
    </div-->
  </div>
</template>

<script>
import BaseActionCard from '@/components/BaseActionCard.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import FormFieldSearch from '@/components/FormFieldSearch.vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import multiMatch from '@/lib/MultiFieldSearch.js';
import form from '@/mixins/form.js';

export default {
  name: 'SerialFieldLibrary',

  components: {
    BaseDialog,
    FormFieldSearch,
    BaseActionCard,
    LoadingSignal,
  },

  mixins: [form],

  emits: ['reload'],

  data() {
    return {
      data_ready: false,
      search_text: undefined,
      field_list: [],
      show_new_field_form: false,
      show_delete: false,
    };
  },

  computed: {
    selected_field_key() {
      return this.$route.params.field_key;
    },

    selected_field() {
      return this.field_list.find(
        (field) => field._key == this.selected_field_key,
      );
    },

    filtered_fields() {
      const fields_to_search = ['name', 'hint', 'label'];
      return this.field_list.filter((field) =>
        multiMatch(this.search_text, field, fields_to_search),
      );
    },
  },

  created() {
    this.getFields();
  },

  methods: {
    showFieldDetail(field_key) {
      this.$router.push({
        name: 'serialFieldDetail',
        params: { field_key },
      });
    },
    getFields() {
      this.$api.get('serial-field').then((resp) => {
        this.field_list = resp.data.sort();
        this.data_ready = true;
      });
    },

    addField(customField) {
      this.show_new_field_form = false;
      let field = customField;
      customField.use_in_serial = true;
      this.$api
        .put(`field/${field._key}`, {
          ...field,
          ...customField,
        })
        .then(() => {
          this.$emit('reload');
          this.getFields();
        });
    },

    deleteField() {
      this.show_delete = false;
      let temp_data = this.selected_field;
      temp_data.use_in_serial = false;
      this.$api
        .put(`field/${temp_data._key}`, {
          ...this.field,
          ...temp_data,
        })
        .then(() => {
          this.$q.notify({
            message: this.$t('field_delete_success'),
            color: 'theme-green',
            timeout: 1500,
            position: 'top',
          });
          this.$emit('reload');
          this.getFields();
        });
    },
  },
};
</script>

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

      <!-- ISSUE TYPE LIST -->
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

      <!-- ISSUE TYPE LIST COUNT -->
      <div class="row flex-center smaller q-py-xs">
        {{ filtered_fields.length }} {{ $t('of') }} {{ field_list.length }}
      </div>

      <div class="q-pa-md q-mt-auto">
        <q-btn
          class="full-width q-mt-auto"
          color="theme-blue"
          :label="$t('new')"
          @click="show_new_field_form = true"
        >
        </q-btn>
      </div>
    </div>

    <BaseDialog :show="show_new_field_form" :no-backdrop-dismiss="false">
      <FormFieldNew @close="show_new_field_form = false" @created="getFields">
      </FormFieldNew>
    </BaseDialog>

    <q-separator vertical />

    <!-- FIELD DATA -->
    <div v-if="data_ready" class="col full-height">
      <router-view :field="selected_field" @reload="getFields"> </router-view>
    </div>
  </div>
</template>

<script>
import BaseDialog from '@/components/BaseDialog.vue';
import FormFieldNew from '@/components/FormFieldNew.vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import multiMatch from '@/lib/MultiFieldSearch.js';
import form from '@/mixins/form.js';

export default {
  name: 'SerialFieldLibrary',

  components: {
    BaseDialog,
    FormFieldNew,
    LoadingSignal,
  },

  mixins: [form],

  data() {
    return {
      data_ready: false,
      search_text: undefined,
      field_list: [],
      show_new_field_form: false,
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
        name: 'formFieldDetail',
        params: { field_key },
      });
    },
    getFields() {
      this.$api.get('field').then((resp) => {
        this.field_list = resp.data.sort();
        this.data_ready = true;
      });
    },
  },
};
</script>

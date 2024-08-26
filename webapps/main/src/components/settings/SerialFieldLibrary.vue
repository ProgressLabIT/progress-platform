<template>
  <LoadingSignal v-if="!data_ready" />

  <div v-else class="row full-height">
    <div class="full-height column col">
      <div class="row justify-between q-pr-md">
        <!-- <q-input
          v-model="search_text"
          :dense="dense"
          :readonly="!editMode"
          filled
          class="q-px-md q-pt-md col-5"
          :placeholder="$capitalize($t('search'))"
        >
          <template #append>
            <q-icon name="mdi-magnify" />
          </template>
        </q-input>
          <q-btn
          v-if="!edit_mode"
          icon='mdi-pencil'
          round
          padding="md md"
          flat
          @click="edit_mode = true"
        />
        <div class="col-auto" v-else>
          <q-btn
            color="theme-blue"
            :label="$t('save')"
          />
          <q-btn
            color="theme-grey"
            :label="$t('cancel')"
          />
        </div> -->
      </div>

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
          :dense="dense"
          :readonly="!editMode"
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

      <div class="row q-pa-md justify-between">
        <q-btn
          v-if="editMode"
          color="theme-blue"
          class="col-auto"
          size="12px"
          :label="$t('add_field')"
          @click="show_new_field_form = true"
        >
        </q-btn>
        <q-btn
          v-if="selected_field_key && editMode"
          color="theme-red"
          class="col-auto"
          size="12px"
          :label="$t('remove_field')"
          :readonly="!editMode"
          @click="show_delete = true"
        >
        </q-btn>
      </div>
    </div>

    <BaseDialog
      :show="show_new_field_form"
      :no-backdrop-dismiss="false"
      @close="show_new_field_form = false"
    >
      <FormFieldSearch @close="show_new_field_form = false" @select="addField">
      </FormFieldSearch>
    </BaseDialog>

    <BaseDialog
      :show="show_delete"
      :no-backdrop-dismiss="false"
      @close="show_delete = false"
    >
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

  props: {
    editMode: {
      type: Boolean,
      required: true,
    },
    dense: {
      type: Boolean,
      default: false,
    },
    field_list: {
      type: Array,
      default: () => [],
    },
  },

  emits: ['reload', 'update:field_list'],

  data() {
    return {
      data_ready: true,
      search_text: undefined,
      show_new_field_form: false,
      show_delete: false,
      selected_field_key: '',
    };
  },

  computed: {
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

  methods: {
    showFieldDetail(field_key) {
      this.selected_field_key =
        this.selected_field_key == field_key ? null : field_key;
    },

    addField(customField) {
      this.show_new_field_form = false;
      let field = customField;
      let temp_values = this.field_list;
      temp_values.push(field);
      this.$emit('update:field_list', temp_values);
      this.$emit('reload');
    },

    deleteField() {
      this.show_delete = false;
      let field = this.selected_field;
      let temp_values = this.field_list;
      temp_values.pop(field);
      this.$emit('update:field_list', temp_values);
      this.$emit('reload');
    },
  },
};
</script>

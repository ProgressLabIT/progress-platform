<template>
  <q-splitter v-model="splitter_model">
    <template #before>
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
        <div class="col-2">
          {{ $t('type') }}
        </div>
        <div class="col">
          {{ $t('name') }}
        </div>
      </div>

      <q-separator />

      <!-- ISSUE TYPE LIST -->
      <q-scroll-area class="col">
        <div
          v-for="(field, index) in filtered_fields"
          :key="field._key"
          class="row pointer q-px-lg q-py-xs medium full-width"
          :class="{
            'alternate-row': index % 2 === 0,
            'bg-blue-backdrop': field._key == selected_field_key,
          }"
          style="white-space: nowrap"
          @click="showFieldDetail(field._key)"
        >
          <div class="col-2">
            <q-icon :name="getFieldIcon(field.type)" />
          </div>
          <div class="col ellipsis">
            {{ $capitalize(field.name) }}
          </div>
        </div>
      </q-scroll-area>

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

    <BaseDialog
      :show="show_new_field_form"
      :no-backdrop-dismiss="false"
      @close="show_new_field_form = false"
    >
      <FormFieldNew @close="show_new_field_form = false">
      </FormFieldNew>
    </BaseDialog>

    </template>
    <template #after>

    <div class="col full-height">
      <router-view
        v-if="!selected_field_key || selected_field"
        :key="String(selected_field_key ?? '')"
        :field="selected_field"
        @reload="refreshFields"
      />
    </div>
  </template>
  </q-splitter>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import BaseDialog from '@/components/BaseDialog.vue';
import FormFieldNew from '@/components/FormFieldNew.vue';
import { useFormFields } from '@/composables/form.js';
import multiMatch from '@/lib/MultiFieldSearch.js';
import { useStore } from 'vuex';

const route = useRoute();
const router = useRouter();
const store = useStore();
const { getFieldIcon } = useFormFields();

const search_text = ref(undefined);
const show_new_field_form = ref(false);
const splitter_model = ref(30);

const selected_field_key = computed(() => route.params.field_key);

const field_list = computed(() => {
  const fields = [...store.state.form.customFields];
  return fields.sort((a, b) =>
    String(a.name ?? '').localeCompare(String(b.name ?? ''), undefined, {
      sensitivity: 'base',
    }),
  );
});

const selected_field = computed(() => {
  const key = selected_field_key.value;
  if (key == null || key === '') {
    return undefined;
  }
  return store.getters.getCustomFieldByKey(String(key));
});

function refreshFields() {
  return store.dispatch('getCustomFields');
}

const filtered_fields = computed(() => {
  const fields_to_search = ['name', 'hint', 'label'];
  return field_list.value.filter((field) =>
    multiMatch(search_text.value, field, fields_to_search),
  );
});

function showFieldDetail(field_key) {
  router.push({
    name: 'formFieldDetail',
    params: { field_key },
  });
}

</script>

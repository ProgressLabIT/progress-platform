<template>
  <BaseModalScreen :show="true" @close="exit">
    <template #header>
      <q-btn
        v-if="!no_hierarchy"
        dense
        unelevated
        icon="mdi-file-tree"
        @click="
          () => {
            mini_state = !mini_state;
            if (mini_state) serial_detail_splitted_width = 1;
            else serial_detail_splitted_width = 30;
          }
        "
      />
      <span
        class="q-ml-md display medium highlight weight-medium text-uppercase"
      >
        {{ $t('serial_id') }}: {{ serialKey }}
      </span>
      <q-space></q-space>
    </template>

    <template #content>
      <q-splitter
        v-model="data_column_width"
        class="full-width full-height q-pt-sm"
        separator-class="text-disabled"
      >
        <template #before>
          <div class="row full-width full-height">
            <div v-if="!mini_state" class="col-auto column full-height scroll">
                <SerialTree
                  :serial_key="serialKey"
                  :mini_state="mini_state"
                  :edit_mode="editMode"
                  @select="(selected_key) => onSerialSelection(selected_key)"
                  @no-nodes="no_hierarchy = true"
                />
              </div>
            <div class="col column q-py-md full-height">
              <div class="col">
                <SerialDetailForm
                  :serial_key="serialKey"
                  :edit_mode="editMode"
                />
              </div>
              <div class="col-auto row q-gutter-md q-px-md q-pt-md justify-end">
                <q-btn
                  v-if="!editMode && can_edit"
                  color="theme-blue"
                  :label="$t('print')"
                  @click="requestDHRPrint"
                >
                </q-btn>

                <q-btn
                  v-if="!editMode && can_edit"
                  color="theme-orange"
                  :label="$t('edit')"
                  @click="editMode = true"
                >
                </q-btn>

                <q-btn
                  v-if="user_can_delete && !editMode"
                  color="theme-red"
                  size="12px"
                  icon="mdi-delete"
                  :label="$t('delete')"
                  @click="deleteSerial"
                >
                </q-btn>
                <q-btn
                  v-if="editMode"
                  size="12px"
                  color="theme-orange"
                  :label="$t('save')"
                  :loading="saving"
                  :disable="!can_edit"
                  @click="save"
                >
                </q-btn>
                <q-btn
                  v-if="editMode"
                  size="12px"
                  color="theme-grey"
                  :label="$t('cancel')"
                  :loading="saving"
                  @click="onDialogCancel"
                >
                </q-btn>
              </div>
            </div>
          </div>
        </template>

        <!-- RIGHT SECTION -->
        <template #after>
          <MessageThread
            :messages="messages"
            context="serial"
            :context_key="serialKey"
          >
            <template #header>
              <div class="display low-text text-h5 col-auto q-pb-md">
                {{ $t('message', 2) }}
              </div>
              <q-separator></q-separator>
            </template>
          </MessageThread>
        </template>
      </q-splitter>
    </template>
  </BaseModalScreen>
</template>

<script setup>
import { cloneDeep } from 'lodash';
import { useQuasar } from 'quasar';
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute, useRouter } from 'vue-router';
import { useStore } from 'vuex';
import { api } from '@/boot/axios.js';
import BaseModalScreen from '@/components/BaseModalScreen.vue';
import MessageThread from '@/components/MessageThread.vue';
import SerialDetailForm from '@/components/traceability/SerialDetailForm.vue';
import SerialTree from '@/components/traceability/SerialTree.vue';
import { sendEvent } from '@/composables/event.js';
import { useConfigStore } from '../../stores/config';

const props = defineProps({
  // from router
  serialKey: {
    type: String,
    required: true,
  },
});

// Composables
const store = useStore();
const { t } = useI18n();
const $q = useQuasar();
const route = useRoute();
const router = useRouter();
const { config } = useConfigStore();

// Reactive data
const messages = ref([]);
const data_column_width = ref(65);
const serial_detail_splitted_width = ref(30);
const mini_state = ref(false);
const no_hierarchy = ref(false);
const selected = ref(null);
const editMode = ref(false);
const saving = ref(false);

// Computed properties
const serial = computed(() => store.getters.getSerialData(props.serialKey));
const session_data = computed(() => store.state.session);
const user_can_delete = computed(() => (
  store.getters.hasPermission('production') &&
  !store.getters.getSerialData(props.serialKey)?.deleted &&
  config.allowSerialDelete
));
const can_edit = computed(() => !serial.value?.deleted);

// Methods
function exit() {
  if (route.query.back_to) {
    let query = { ...route.query };
    delete query.back_to;
    router.push({ name: route.query.back_to, query });
  } else {
    router.back();
  }
}

function getFieldType(field) {
  return store.getters.getCustomFieldByKey(field.custom_field_key)?.type;
}

function missingMandatoryValues(form_data) {
  let missing_mandatory_fields = false;
  if (!form_data) {
    return missing_mandatory_fields;
  }
  form_data.forEach((field) => {
    let type = getFieldType(field);
    if (
      type !== 'ternary' &&
      field.mandatory &&
      (!field.value || field.value === null || field.value === '' || field.value?.length === 0)
    ) {
      missing_mandatory_fields = true;
    }
  });
  return missing_mandatory_fields;
}

async function saveFiles(serial_key) {
  let form_fields = serial.value.data || [];

  const promises = form_fields
    .filter((field) => getFieldType(field) === 'files')
    .map(async (field) => {
      const to_delete = [];
      const to_add = [];

      field.value?.forEach((file) => {
        if (file.temp) {
          to_add.push(file.content);
        } else if (file.delete && file.bucket !== 'traceability') {
          to_delete.push(file.name);
        }
      });

      const target = {
        bucket: 'serial',
        object_key: serial_key,
        subfolder: field.form_field_key,
      };

      // Upload new files
      if (to_add.length) {
        // Populate form data
        const add_body = new FormData();
        Object.entries(target).forEach(([k, v]) => add_body.append(k, v));
        to_add.forEach((file) => add_body.append('contents', file));
        // Post files
        try {
          await api.post('/files', add_body);
        } catch (error) {
          console.error(error);
          window.alert(error);
        }
      }

      // Delete files
      if (to_delete.length) {
        try {
          await api.delete('/files', {
            data: {
              ...target,
              filenames: to_delete,
            },
          });
        } catch (error) {
          console.error(error);
          window.alert(error);
        }
      }
    });

  return Promise.all(promises);
}

async function save() {
  saving.value = true;

  let serial_data = cloneDeep(serial.value);
  if (serial.value?.data) {
    let form_data = [];
    for (const field_data of serial.value.data) {
      form_data.push({
        form_field_key: field_data.form_field_key,
        custom_field_key: field_data.custom_field_key,
        label: field_data.label,
        hint: field_data.hint,
        mandatory: field_data.mandatory,
        value:
          getFieldType(field_data) === 'files'
            ? field_data.value
                ?.filter((file) => !file.delete)
                .map(({ size, name }) => ({ size, name }))
            : field_data.value,
      });
    }
    serial_data.data = form_data;
  }

  if (serial.value.released && missingMandatoryValues(serial.value.data)) {
    // Enable updating partial data if serial is not released
    window.alert(t('fill_mandatory_fields'));
    saving.value = false;
    return;
  }

  serial_data.updated_by = `User/${session_data.value.user._key}`; // temporarily hardcoding DB id

  try {

    await saveFiles(serial_data._key);
    await sendEvent({
      event_type: 'SERIAL_UPDATED',
      event_data: {
        serial_key: serial_data._key,
        serial_code: serial_data.code,
        serial_data: serial_data.data
      }
    });
    await refreshSerial();
  } catch (error) {
    console.error('Error updating serial:', error);
  }

  editMode.value = false;
  saving.value = false;
}

function refreshSerial() {
  store.dispatch('updateSerials', { serial_key: props.serialKey });
}

async function onDialogCancel() {
  refreshSerial();
  editMode.value = false;
}

function goToSerial(serialKey) {
  const to_route = {
    name: 'serialDetail',
    params: { serialKey },
    query: {
      back_to: route.name,
      ...route.query,
    },
  };
  router.push(to_route);
}

async function onSerialSelection(selected_key) {
  // Fetch data from server is serial data is not present
  if (!store.getters.getSerialData(selected_key)) {
    await store.dispatch('appendSerial', { serial_key: selected_key });
    goToSerial(selected_key);
  } else {
    goToSerial(selected_key);
  }
}

function deleteSerial() {
  $q
    .dialog({
      cancel: true,
      title: t('serial_delete_confirm_title'),
      message: t('serial_delete_confirm_question'),
      options: {
        type: 'toggle',
        modelValue: '',
        // inline: true
        items: [
          {
            label: t('serial_delete_also_children'),
            value: 'delete_children',
          },
        ],
      },
    })
    .onOk(async (delete_children) => {
      await sendEvent({
        event_type: 'SERIAL_DELETED',
        event_data: {
          delete_children: delete_children,
          serial_key: serial.value._key,
        }
      });
      await store.dispatch('loadSerials');
      $q.notify({
        message: t(`Seriale ${serial.value.code} eliminato`),
        color: 'theme-orange',
        position: 'top',
      });
      exit();
    });
}

async function requestDHRPrint() {
  $q.dialog({
    title: t('dhr.options'),
    message: t('dhr.select_options'),
    class: 'background',
    color: 'theme-blue',
    options: {
      type: 'checkbox',
      model: ['include_step_data'],
      items: [
        {
          label: t('dhr.include_step_data'),
          value: 'include_step_data'
        },
        {
          label: t('dhr.include_attachments'),
          value: 'include_attachments'
        },
        {
          label: t('dhr.include_children'),
          value: 'include_children'
        },
      ],
    },
    cancel: true,
    persistent: true
  }).onOk(async (input) => {
    $q.loading.show();
    try {
      const includeAttachments = input.includes('include_attachments');
      const includeChildren = input.includes('include_children');
      const includeStepData = input.includes('include_step_data');
      const params = { include_attachments: includeAttachments, include_children: includeChildren, include_step_data: includeStepData }
      const resp = await api.get(`serial/${props.serialKey}/dhr`, { responseType: 'blob', params })
      console.log('resp.headers', resp.headers)

      // Extract filename from Content-Disposition header
      const contentDisposition = resp.headers['content-disposition'];
      console.log('Content-Disposition', contentDisposition)
      let filename = `DHR_${serial.value.code}_${new Date().toISOString().split('T')[0]}.pdf`; // fallback

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="([^"]+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      const blob = new Blob([resp.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename; // Use the extracted filename
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      $q.notify({
        message: error.message,
        color: 'theme-red',
        position: 'top',
      });
    } finally {
      $q.loading.hide();
    }
  }).onCancel(() => {
    return;
  });
}

// Lifecycle
onMounted(() => {
  editMode.value = false;
  saving.value = false;
  selected.value = null;
  store.dispatch('loadUsers');
  store.dispatch('appendSerial', { serial_key: props.serialKey });
});
</script>

<style lang="sass" scoped>
.dot
  height: 13px
  width: 13px
  border-radius: 100%
  background-color: #888
  border: 5px solid var(--surface-1)
  box-sizing: content-box
  z-index:99

.thread
  position: absolute
  height: 100%
  left: 11px
  top: 20px
  width: 1px
  background-color: #fff3
</style>

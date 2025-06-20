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

<script>
import { cloneDeep } from 'lodash';
import BaseModalScreen from '@/components/BaseModalScreen.vue';
import MessageThread from '@/components/MessageThread.vue';
import SerialDetailForm from '@/components/traceability/SerialDetailForm.vue';
import SerialTree from '@/components/traceability/SerialTree.vue';
import { timestamp } from '@/lib/TimeHandling.js';
import { useConfigStore } from '../../stores/config';

export default {
  name: 'SerialDetail',

  components: {
    BaseModalScreen,
    MessageThread,
    SerialTree,
    SerialDetailForm,
  },

  props: {
    // from router
    serialKey: {
      type: String,
      required: true,
    },
  },

  setup() {
    const { config } = useConfigStore();
    return {
      config,
    };
  },

  data() {
    return {
      messages: [],
      data_column_width: 65,
      serial_detail_splitted_width: 30,
      mini_state: false,
      no_hierarchy: false,
      selected: null,
      editMode: false,
      saving: false,
    };
  },

  computed: {
    serial() {
      return this.$store.getters.getSerialData(this.serialKey);
    },

    session_data() {
      return this.$store.state.session;
    },

    user_can_delete() {
      return (
        this.$store.getters.hasPermission('production') &&
        !this.$store.getters.getSerialData(this.serialKey)?.deleted &&
        this.config.allowSerialDelete
      );
    },

    can_edit() {
      return !this.serial?.deleted;
    },
  },

  created() {
    this.editMode = false;
    this.saving = false;
    this.selected = null;
    this.$store.dispatch('loadUsers');
    this.$store.dispatch('appendSerial', { serial_key: this.serialKey });
  },

  methods: {
    exit() {
      if (this.$route.query.back_to) {
        let query = { ...this.$route.query };
        delete query.back_to;
        this.$router.push({ name: this.$route.query.back_to, query });
      } else {
        this.$router.back();
      }
    },

    getFieldType(field) {
      return this.$store.getters.getCustomFieldByKey(field.custom_field_key)
        ?.type;
    },

    missingMandatoryValues(form_data) {
      let missing_mandatory_fields = false;
      if (!form_data) {
        return missing_mandatory_fields;
      }
      form_data.forEach((field) => {
        let type = this.getFieldType(field);
        if (
          type !== 'ternary' &&
          field.mandatory &&
          (!field.value || field.value === null || field.value === '' || field.value?.length === 0)
        ) {
          missing_mandatory_fields = true;
        }
      });
      return missing_mandatory_fields;
    },

    async saveFiles(serial_key) {
      let form_fields = this.serial.data;

      const promises = form_fields
        .filter((field) => this.getFieldType(field) === 'files')
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
              await this.$api.post('/files', add_body);
            } catch (error) {
              console.error(error);
              window.alert(error);
            }
          }

          // Delete files
          if (to_delete.length) {
            try {
              await this.$api.delete('/files', {
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
    },

    async save() {
      this.saving = true;

      let serial_data = cloneDeep(this.serial);
      if (this.serial?.data) {
        let form_data = [];
        for (const field_data of this.serial.data) {
          form_data.push({
            form_field_key: field_data.form_field_key,
            custom_field_key: field_data.custom_field_key,
            value:
              this.getFieldType(field_data) === 'files'
                ? field_data.value
                    ?.filter((file) => !file.delete)
                    .map(({ size, name }) => ({ size, name }))
                : field_data.value,
          });
        }
        serial_data.data = form_data;
      }

      if (this.serial.released && this.missingMandatoryValues(this.serial.data)) {
        // Enable updating partial data if serial is not released
        window.alert(this.$t('fill_mandatory_fields'));
        this.saving = false;
        return;
      }

      const user = this.session_data.user._key;

      serial_data.updated_by = `User/${user}`; // temporarily hardcoding DB id

      const event = {
        event_type: 'SERIAL_UPDATED',
        user_key: user,
        user_session_key: this.session_data.session_key,
        timestamp: timestamp(),
        serial_key: serial_data._key,
        serial_code: serial_data.code,
        serial_data: serial_data.data
      };

      await this.saveFiles(serial_data._key);
      await this.$api.post('event', event);
      this.refreshSerial();

      this.editMode = false;
      this.saving = false;
    },

    refreshSerial() {
      this.$store.dispatch('updateSerials', { serial_key: this.serialKey });
    },

    async onDialogCancel() {
      this.refreshSerial();
      this.editMode = false;
    },

    goToSerial(serialKey) {
      const to_route = {
        name: 'serialDetail',
        params: { serialKey },
        query: {
          back_to: this.$route.name,
          ...this.$route.query,
        },
      };
      this.$router.push(to_route);
    },

    async onSerialSelection(selected_key) {
      // Fetch data from server is serial data is not present
      if (!this.$store.getters.getSerialData(selected_key)) {
        await this.$store.dispatch('appendSerial', { serial_key: selected_key })
        this.goToSerial(selected_key);
      } else {
        this.goToSerial(selected_key);
      }
    },

    deleteSerial() {
      this.$q
        .dialog({
          cancel: true,
          title: this.$t('serial_delete_confirm_title'),
          message: this.$t('serial_delete_confirm_question'),
          options: {
            type: 'toggle',
            modelValue: '',
            // inline: true
            items: [
              {
                label: this.$t('serial_delete_also_children'),
                value: 'delete_children',
              },
            ],
          },
        })
        .onOk(async (delete_children) => {
          const user = this.session_data.user._key;
          const event = {
            event_type: 'SERIAL_DELETED',
            user_key: user,
            user_session_key: this.session_data.session_key,
            timestamp: timestamp(),
            delete_children: delete_children,
            serial_key: this.serial._key,
          };

          await this.$api.post('event', event);
          await this.$store.dispatch('loadSerials');
          this.$q.notify({
            message: this.$t(`Seriale ${this.serial.code} eliminato`),
            color: 'theme-orange',
            position: 'top',
          });
          this.exit();
        });
    },
  },
};
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

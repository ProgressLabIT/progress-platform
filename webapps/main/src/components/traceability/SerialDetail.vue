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
        {{ $t('serial_id') }}: {{ selected_serial }}
      </span>

      <q-space></q-space>

      <div class="row q-gutter-md">
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
        <q-btn
          v-if="!editMode"
          size="12px"
          icon="mdi-keyboard-return"
          color="theme-grey"
          :label="$t('back')"
          @click="exit"
        >
        </q-btn>
      </div>
    </template>

    <template #content>
      <q-splitter
        v-model="data_column_width"
        class="fit q-py-sm"
        separator-class="text-disabled"
      >
        <template #before>
          <q-splitter
            v-if="!mini_state && !no_hierarchy"
            v-model="serial_detail_splitted_width"
          >
            <template #before>
              <div class="q-pa-md">
                <SerialTree
                  :serial_key="selected_serial"
                  :mini_state="mini_state"
                  :edit_mode="editMode"
                  @select="(value) => (selected = value)"
                  @no-nodes="no_hierarchy = true"
                ></SerialTree>
              </div>
            </template>

            <template #after>
              <SerialDetailForm
                :serial_key="selected_serial"
                :edit_mode="editMode"
              ></SerialDetailForm>
            </template>
          </q-splitter>
          <SerialDetailForm
            v-else
            :serial_key="selected_serial"
            :edit_mode="editMode"
          ></SerialDetailForm>
        </template>

        <!-- RIGHT SECTION -->
        <template #after>
          <MessageThread
            :messages="messages"
            context="serial"
            :context_key="selected_serial"
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
import BaseModalScreen from '@/components/BaseModalScreen.vue';
import MessageThread from '@/components/MessageThread.vue';
import SerialDetailForm from '@/components/traceability/SerialDetailForm.vue';
import SerialTree from '@/components/traceability/SerialTree.vue';
import { timestamp } from '@/lib/TimeHandling.js';

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
    selected_serial() {
      if (this.selected) {
        return this.selected;
      }
      return this.serialKey;
    },

    main_selected() {
      return this.selected === null || this.selected === this.serialKey;
    },

    serial() {
      return this.$store.getters.getSerialData(this.serialKey);
    },

    session_data() {
      return this.$store.state.session;
    },

    user_can_delete() {
      return (
        this.$store.getters.hasPermission('production') &&
        !this.$store.getters.getSerialData(this.serialKey).deleted &&
        this.main_selected
      );
    },

    can_edit() {
      return (
        !this.$store.getters.getSerialData(this.serialKey).deleted &&
        this.main_selected
      );
    },
  },

  created() {
    this.editMode = false;
    this.saving = false;
    this.selected = null;
    this.$store.dispatch('loadUsers');
  },

  methods: {
    exit() {
      this.$router.back();
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
          (!field.value || field.value === null || field.value === '')
        ) {
          missing_mandatory_fields = true;
        }
      });
      return missing_mandatory_fields;
    },

    async save() {
      this.saving = true;

      let serial_data = this.serial;

      if (this.missingMandatoryValues(this.serial.data)) {
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
        serial_data,
      };

      await this.$api.post('event', event);

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

    deleteSerial() {
      this.$q
        .dialog({
          cancel: true,
          title: this.$t('serial_delete_confirm_title'),
          message: this.$t('serial_delete_confirm_question'),
        })
        .onOk(() => {
          const user = this.session_data.user._key;

          const event = {
            event_type: 'SERIAL_DELETED',
            user_key: user,
            user_session_key: this.session_data.session_key,
            timestamp: timestamp(),
            serial_data: {
              _key: this.serial._key,
            },
          };

          this.$api.post('event', event);
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

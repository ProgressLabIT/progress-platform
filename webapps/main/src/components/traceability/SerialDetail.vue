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
                  @select="(value) => (selected = value)"
                  @no-nodes="no_hierarchy = true"
                ></SerialTree>
              </div>
            </template>

            <template #after>
              <SerialDetailForm
                :serial_key="selected_serial"
                @exit="exit"
              ></SerialDetailForm>
            </template>
          </q-splitter>
          <SerialDetailForm
            v-else
            :serial_key="selected_serial"
            @exit="exit"
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
    };
  },

  computed: {
    selected_serial() {
      if (this.selected) {
        return this.selected;
      }
      return this.serialKey;
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

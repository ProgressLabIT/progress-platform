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
            if (mini_state) position_detail_splitted_width = 1;
            else position_detail_splitted_width = 30;
          }
        "
      />
      <span
        class="q-ml-md display medium highlight weight-medium text-uppercase"
      >
        {{ $t('warehouse.position.code') }}: {{ position.code }}
      </span>
      <q-space></q-space>
    </template>

    <template #content>
      <q-splitter
        v-model="data_column_width"
        class="fit q-pt-sm"
        separator-class="text-disabled"
      >
        <template #before>
          <div class="row full-height">
            <template v-if="!mini_state">
              <div class="col-auto full-height">
                <PositionTree
                  :position_key="position._key"
                  :mini_state="mini_state"
                  :edit_mode="editMode"
                  @select="(selected_key) => onPositionSelection(selected_key)"
                  @no-nodes="no_hierarchy = true"
                />
              </div>
              <q-separator vertical></q-separator>
            </template>
            <div class="col column q-py-md">
              <div class="col">
                <PositionDetailForm
                  :position_key="position._key"
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
                  @click="deletePosition"
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
        <template #after> </template>
      </q-splitter>
    </template>
  </BaseModalScreen>
</template>

<script>
import { cloneDeep } from 'lodash';
import BaseModalScreen from '@/components/BaseModalScreen.vue';
import PositionDetailForm from '@/components/warehouse/position/PositionDetailForm.vue';
import PositionTree from '@/components/warehouse/position/PositionTree.vue';

export default {
  name: 'PositionDetail',

  components: {
    BaseModalScreen,
    PositionDetailForm,
    PositionTree,
  },

  props: {
    // from router
    positionKey: {
      type: String,
      required: true,
    },
  },

  data() {
    return {
      data_column_width: 65,
      position_detail_splitted_width: 30,
      mini_state: false,
      no_hierarchy: false,
      selected: null,
      editMode: false,
      saving: false,
    };
  },

  computed: {
    position() {
      return this.$store.getters.getPositionData(this.positionKey);
    },

    session_data() {
      return this.$store.state.session;
    },

    user_can_delete() {
      return (
        this.$store.getters.hasPermission('production') &&
        !this.$store.getters.getPositionData(this.positionKey).deleted
      );
    },

    can_edit() {
      return !this.$store.getters.getPositionData(this.positionKey)?.deleted;
    },
  },

  created() {
    this.editMode = false;
    this.saving = false;
    this.selected = null;
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

    async save() {
      this.saving = true;

      let position_data = cloneDeep(this.position);

      await this.$api.patch(`position/${this.positionKey}`, position_data);

      this.editMode = false;
      this.saving = false;
    },

    async onDialogCancel() {
      this.editMode = false;
    },

    goToPosition(positionKey) {
      const to_route = {
        name: 'positionDetail',
        params: { positionKey },
        query: {
          back_to: this.$route.name,
          ...this.$route.query,
        },
      };
      this.$router.push(to_route);
    },

    async onPositionSelection(selected_key) {
      if (!this.$store.getters.getPositionData(selected_key)) {
        this.$store
          .dispatch('appendPosition', {
            position_key: selected_key,
          })
          .then(this.goToPosition(selected_key));
      } else {
        this.goToPosition(selected_key);
      }
    },

    deletePosition() {
      this.$q
        .dialog({
          cancel: true,
          title: this.$t('position_delete_confirm_title'),
          message: this.$t('position_delete_confirm_question'),
        })
        .onOk(() => {
          this.$api.delete(`position/${this.positionKey}`);
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

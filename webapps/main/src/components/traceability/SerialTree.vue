<template>
  <div v-if="!mini_state" class="q-pa-md q-gutter-sm">
    <q-tree
      id="serial-tree"
      ref="serialNodes"
      v-model:selected="selected"
      :nodes="nodes"
      node-key="_key"
      :loading="loading"
      @lazy-load="({ node, done }) => lazyLoad(node, done)"
    >
      <!-- @update:model-value="(selection) => $emit('select', selection)" -->
      <template #default-header="prop">
        <div
          class="row items-center full-width justify-between q-pr-xl"
          @mouseenter="over_key = prop.node._key"
          @mouseleave="over_key = null"
        >
          <div
            :class="{
              'text-disabled': prop.node.replaced && prop.node._key !== selected,
              'text-weight-bold text-high': prop.node._key === selected,
              'text-low': !prop.node.replaced && prop.node._key !== selected,
            }"
          >
            {{ prop.node.product_code }}
          </div>
          <div class="absolute-right q-py-xs">
            <q-badge v-if="prop.node.replaced" color="theme-grey" outline>
              <q-icon name="mdi-link-off" size="12px" />
            </q-badge>
          </div>
          <q-btn
            v-if="prop.node.parent_key && !prop.node.replaced && !edit_mode"
            v-show="over_key === prop.node._key"
            flat
            round
            size="xs"
            class="absolute-right"
            @click.stop="editComponentLink(prop.node)"
          >
            <q-icon name="mdi-pencil" size="xs" />
          </q-btn>
          <q-tooltip
            v-if="prop.node.product_description"
            anchor="bottom middle"
            self="top middle"
          >
            {{ prop.node.product_description }}
          </q-tooltip>
        </div>
      </template>

      <template #default-body="prop">
        <div
          :class="{
            'text-weight-bold': prop.node._key === selected,
            'text-disabled': prop.node.replaced,
          }"
        >
          # {{ prop.node.code }}
        </div>
      </template>
    </q-tree>
  </div>
</template>

<script>
import { Dialog } from 'quasar';
import SerialComponentLinkEditDialog from '@/components/traceability/SerialComponentLinkEditDialog.vue';
import sendEvent from '@/mixins/event.js';

export default {
  name: 'SerialTree',

  mixins: [sendEvent],

  props: {
    mini_state: {
      type: Boolean,
      default: false,
    },
    edit_mode: {
      type: Boolean,
      default: false,
    },
    serial_key: {
      type: String,
      required: true,
    },
  },

  emits: ['select', 'noNodes'],

  data() {
    return {
      drawer: true,
      loading: false,
      selected: null,
      over_key: null,
      nodes_data: [],
    };
  },

  computed: {
    session_data() {
      return this.$store.state.session;
    },

    nodes() {
      return this.nodes_data.map((n) => this.convertNode(n, undefined));
    },
  },

  watch: {
    selected: {
      handler(serial_key) {
        if (!serial_key) {
          this.selected = this.nodes[0]._key;
        }
        this.$emit('select', this.selected);
      },
    },
  },

  created() {
    this.getSerialHierarcy();
    setTimeout(() => {
      if (this.$refs.serialNodes) {
        this.$refs.serialNodes.expandAll();
      }
    }, 500);
  },

  methods: {
    async lazyLoad(node, done) {
      let children = await this.getChildren(node.key);
      setTimeout(() => {
        done(children);
      }, 1000);
    },

    async showSerialDetails(serialKey) {
      await this.$store.dispatch('appendSerial', {serial_key: serialKey});
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

    getChildren(node, parent_key) {
      let child_data = [];

      for (const child_node of node) {
        child_data.push(this.convertNode(child_node, parent_key));
      }

      return child_data;
    },

    convertNode(node, parent_key) {
      let children_data = [];
      let expandable = false;
      if (node?.children) {
        children_data = this.getChildren(node.children, node.serial_key);
        expandable = true;
      }
      return {
        _key: node.serial_key,
        parent_key: parent_key,
        code: node.serial_code,
        lazy: false,
        expandable: expandable,
        selectable: this.edit_mode ? false : true,
        children: children_data,
        replaced: node.replaced,
        product_key: node.product_key,
        product_code: node.product_code,
        product_description: node.product_description,
      };
    },

    async getSerialHierarcy() {
      this.loading = true;

      const { data } = await this.$api.get('serial-hierarchy', {
        params: {
          serial_key: this.serial_key,
        },
      });

      this.selected = this.serial_key;

      this.selected = this.serial_key;

      this.nodes_data = data;

      if (!this.nodes_data.length) {
        this.$emit('noNodes', this.selected);
      }

      this.loading = false;
    },

    editComponentLink(node) {
      // Add serial parent and child to store, then show dialog
      const promises = [
        this.$store.dispatch('appendSerial', {serial_key: node.parent_key}),
      ]
      if (node._key) {
        // fetch data only if there's a linked serial
        promises.push(this.$store.dispatch('appendSerial', {serial_key: node._key}))
      }
      Promise.all(promises).then((values) => {
        this.showEditComponentLink(node, values[0])
      });
    },

    showEditComponentLink(node, parentSerial) {
      let serialModel = {
        _key: node._key,
        code: node.code,
        product_key: node.product_key,
        wo_key: parentSerial.wo_key,
        reason: '',
      };

      Dialog.create({
        component: SerialComponentLinkEditDialog,
        componentProps: {
          node: node,
          serial: serialModel,
        },

      }).onOk((newValues) => {
        this.saveNewComponentLink(node, newValues);
      });
    },

    async saveNewComponentLink(node, newValues) {
      const sharedEventData = {
        component_key: node.product_key,
        parent_serial_key: node.parent_key,
      };

      if (newValues) {
        if (node._key) {
          await this.sendEvent({
            event_type: 'SERIAL_UNLINKED',
            event_data: {
              ...sharedEventData,
              child_serial_key: node._key,
              reason: newValues.reason,
              process_inventory: newValues.processInventory.oldLink
            }
          });
        }

        const event_data = {
          ...sharedEventData,
          child_serial_key: newValues._key,
          reason: newValues.reason,
          process_inventory: newValues.processInventory.newLink
        }

        if (newValues.used) {
          event_data.replace_existing = true;
        }

        if (!newValues.available) {
          event_data.process_inventory = false;
        }

        // Link new serial to parent
        await this.sendEvent({
          event_type: 'SERIAL_LINKED',
          event_data,
        });
        this.nodes = [];
        this.getSerialHierarcy();
        setTimeout(() => {
          if (this.$refs.serialNodes) {
            this.$refs.serialNodes.expandAll();
          }
        }, 500);
      }
    },
  },
};
</script>

<style lang="sass">
#serial-tree .q-tree__node-body
  padding-top: 0px !important
</style>

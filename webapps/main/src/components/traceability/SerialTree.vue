<template>
  <div v-if="!mini_state" class="q-pa-md q-gutter-sm">
    <q-tree
      ref="serialNodes"
      id="serial-tree"
      v-model:selected="selected"
      :nodes="nodes"
      node-key="key"
      :loading="loading"
      @lazy-load="({ node, done }) => lazyLoad(node, done)"
    >
      <!-- @update:model-value="(selection) => $emit('select', selection)" -->
      <template #default-header="prop">
        <div
          class="row items-center full-width justify-between q-pr-xl"
          @mouseenter="over_key = prop.node.key"
          @mouseleave="over_key = null"
        >
          <div
            :class="{
              'text-disabled': prop.node.replaced && prop.node.key !== selected,
              'text-weight-bold text-high': prop.node.key === selected,
              'text-primary': !prop.node.replaced && prop.node.key !== selected,
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
            v-show="over_key === prop.node.key"
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
            'text-weight-bold': prop.node.key === selected,
            'text-disabled': prop.node.replaced,
          }"
        >
          # {{ prop.node.label }}
        </div>
      </template>
    </q-tree>
  </div>
</template>

<script>
import { Dialog } from 'quasar';
import SerialComponentLinkEditDialog from '@/components/traceability/SerialComponentLinkEditDialog.vue';
import { timestamp } from '@/lib/TimeHandling.js';

export default {
  name: 'SerialTree',

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
          this.selected = this.nodes[0].key;
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

    showSerialDetails(serialKey) {
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
      let label = node?.serial_code || node.serial_key;
      let children_data = [];
      let expandable = false;
      if (node?.children) {
        children_data = this.getChildren(node.children, node.serial_key);
        expandable = true;
      }
      return {
        key: node.serial_key,
        parent_key: parent_key,
        label: label,
        //lazy: false,
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
      Promise.all([
        this.$store.dispatch('appendSerial', {
          serial_key: node.parent_key,
        }),

        this.$store.dispatch('appendSerial', {
          serial_key: node.key,
        }),
      ]).then((values) => {
        this.showEditComponentLink(node, values[0], values[1]);
      });
    },

    showEditComponentLink(node, parent_serial, serial) {
      let serialModel = {
        _key: serial._key,
        label: serial.code,
        product_key: serial.product_key,
        wo_key: parent_serial.wo_key,
        value: serial._key,
        reason: '',
      };

      let initial_values = [];
      initial_values.push(serialModel);

      Dialog.create({
        component: SerialComponentLinkEditDialog,
        componentProps: {
          node: node,
          serial: serialModel,
          initial_values: initial_values,
        },
      }).onOk((new_values) => {
        this.saveNewComponentLink(node, parent_serial, serial, new_values);
      });
    },

    async saveNewComponentLink(node, parent_serial, serial, new_values) {
      if (new_values) {
        let link_data = [];
        link_data.push({
          wo_key: parent_serial.wo_key,
          component_key: serial.product_key,
          from_serial: node.parent_key,
          to_serial: serial._key,
          reason: new_values.reason,
          replaced: true,
          link_serial_directly: true,
        });

        link_data.push({
          wo_key: parent_serial.wo_key,
          component_key: serial.product_key,
          batch_key: this.batch_key,
          from_serial: node.parent_key,
          to_serial: new_values._key,
          reason: null,
          replaced: false,
          link_serial_directly: true,
        });

        const event = {
          event_type: 'SERIAL_LINKED',
          user_key: this.session_data.session_key,
          timestamp: timestamp(),
          wo_key: serial.wo_key,
          serial_link_data: link_data,
        };

        await this.$api.post('event', event).then(() => {
          this.nodes = [];
          this.getSerialHierarcy();
          setTimeout(() => {
            if (this.$refs.serialNodes) {
              this.$refs.serialNodes.expandAll();
            }
          }, 500);
        });
        //this.$emit('close');
      }
    },
  },
};
</script>
<style lang="sass">
#serial-tree .q-tree__node-body
  padding-top: 0px !important
</style>

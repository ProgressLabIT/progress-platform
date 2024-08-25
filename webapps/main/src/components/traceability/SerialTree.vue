<template>
  <div v-if="!mini_state" class="q-pa-md q-gutter-sm">
    <q-tree
      ref="serialNodes"
      v-model:selected="selected"
      :nodes="nodes"
      node-key="key"
      :loading="loading"
      @lazy-load="({ node, done }) => lazyLoad(node, done)"
    >
      <!-- @update:model-value="(selection) => $emit('select', selection)" -->
      <template #default-header="prop">
        <div
          class="row items-center"
          @mouseenter="dragging ? undefined : (over_key = prop.node.key)"
          @mouseleave="dragging ? undefined : (over_key = prop.node.key)"
        >
          <div
            v-if="prop.node.replaced"
            :class="
              prop.node.key === selected
                ? 'text-weight-bold text-secondary'
                : 'text-secondary'
            "
          >
            {{ `(*) ${prop.node.product_code}` }}
          </div>
          <div
            v-else
            :class="
              prop.node.key === selected
                ? 'text-weight-bold text-primary'
                : 'text-primary'
            "
          >
            {{ prop.node.product_code }}
          </div>
          <q-btn
            v-if="
              prop.node.parent_key &&
              !prop.node.replaced &&
              over_key === prop.node.key &&
              !edit_mode
            "
            flat
            round
            icon="mdi-pencil"
            @click.stop="editComponentLink(prop.node)"
          />
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
        <div>
          <span :class="prop.node.key === selected ? 'text-weight-bold' : ''"
            ># {{ prop.node.label }}
            <q-tooltip
              v-if="prop.node.product_description"
              anchor="bottom middle"
              self="top middle"
            >
              {{ prop.node.product_description }}
            </q-tooltip>
          </span>
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
      nodes: [],
    };
  },

  computed: {
    session_data() {
      return this.$store.state.session;
    },
  },

  watch: {
    selected: {
      handler() {
        if (!this.edit_mode) {
          this.$emit('select', this.selected);
        }
      },
    },
  },

  created() {
    this.initData();
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

    async initData() {
      this.nodes = [];
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
        selectable: true,
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

      let node_data = [];
      for (const parent_node of data) {
        node_data.push(this.convertNode(parent_node, undefined));
      }

      this.nodes = node_data;

      if (this.nodes.length <= 0) {
        this.$emit('noNodes', this.selected);
      }

      this.loading = false;
    },

    async editComponentLink(node) {
      let parent_serial = this.$store.getters.getSerialData(node.parent_key);
      let serial = this.$store.getters.getSerialData(node.key);

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

      let new_values = await new Promise((resolve) => {
        Dialog.create({
          component: SerialComponentLinkEditDialog,
          componentProps: {
            node: node,
            serial: serialModel,
            initial_values: initial_values,
          },
        })
          .onOk((new_values) => resolve(new_values))
          .onCancel(() => resolve(NaN));
      });

      if (new_values) {
        if (!new_values.reason) {
          window.alert(this.$t('serial_field.missing_reason'));
          this.saving = false;
          return;
        }

        let link_data = [];
        link_data.push({
          wo_key: parent_serial.wo_key,
          component_key: serial.product_key,
          from_serial: node.parent_key,
          to_serial: serial._key,
          reason: new_values.reason,
          replaced: true,
        });

        link_data.push({
          wo_key: parent_serial.wo_key,
          component_key: serial.product_key,
          batch_key: this.batch_key,
          from_serial: node.parent_key,
          to_serial: new_values._key,
          reason: null,
          replaced: false,
        });

        const event = {
          event_type: 'SERIAL_LINKED',
          user_key: this.session_data.session_key,
          timestamp: timestamp(),
          wo_key: serial.wo_key,
          serial_link_data: link_data,
        };

        await this.$api.post('event', event);
        this.nodes = [];
        this.getSerialHierarcy();
        setTimeout(() => {
          if (this.$refs.serialNodes) {
            this.$refs.serialNodes.expandAll();
          }
        }, 500);
        //this.$emit('close');
      }
    },
  },
};
</script>

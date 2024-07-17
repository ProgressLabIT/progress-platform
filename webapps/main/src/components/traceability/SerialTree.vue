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
        <div class="row items-center">
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
export default {
  name: 'SerialTree',

  props: {
    mini_state: {
      type: Boolean,
      default: false,
    },
    serial_key: {
      type: String,
      required: true,
    },
  },

  emits: ['select'],

  data() {
    return {
      drawer: true,
      loading: false,
      selected: null,
      nodes: [],
    };
  },

  watch: {
    selected: {
      handler() {
        this.$emit('select', this.selected);
      },
    },
  },

  created() {
    this.initData();
    this.getSerialHierarcy();
    setTimeout(() => {
      this.$refs.serialNodes.expandAll();
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
      this.saving = false;
      this.enableSave = false;
      this.nodes = [];
    },

    async getChildren(serial_key) {
      const { data } = await this.$api.get('serial-childs', {
        params: {
          serial_key: serial_key,
        },
      });

      let child_data = [];

      /*
      "serial_key": "29255965",
    "replaced": null,
    "serial_code": null,
    "product_key": "36136891",
    "product_code": "000 TEST",
    "product_description": ""
      */

      for (const child_node of data) {
        let label = child_node?.serial_code || child_node.serial_key;
        child_data.push({
          key: child_node.serial_key,
          label: label,
          lazy: true,
          expandable: true,
          selectable: true,
          replaced: child_node.replaced,
          product_key: child_node.product_key,
          product_code: child_node.product_code,
          product_description: child_node.product_description,
        });
      }

      return child_data;
    },

    async getSerialHierarcy() {
      this.loading = true;

      const { data } = await this.$api.get('serial-parents', {
        params: {
          serial_key: this.serial_key,
        },
      });

      this.nodes = [];

      this.selected = this.serial_key;
      let children_data = await this.getChildren(this.serial_key);

      for (const parent_node of data.reverse()) {
        let node_data = [];
        let label = parent_node?.serial_code || parent_node.serial_key;
        node_data.push({
          key: parent_node.serial_key,
          label: label,
          lazy: false,
          expandable: true,
          selectable: true,
          children: children_data,
          replaced: parent_node.replaced,
          product_key: parent_node.product_key,
          product_code: parent_node.product_code,
          product_description: parent_node.product_description,
        });

        children_data = node_data;
      }

      this.nodes = children_data;

      this.loading = false;
    },
  },
};
</script>

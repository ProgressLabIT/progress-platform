<template>
  <q-drawer
    v-model="drawer"
    show-if-above
    :mini="!drawer || mini_state"
    :width="500"
    :breakpoint="500"
    bordered
    :class="$q.dark.isActive ? 'bg-grey-9' : 'bg-grey-3'"
    @click.capture="drawerClick"
  >
    <template #mini>
      <q-scroll-area class="fit mini-slot cursor-pointer"> </q-scroll-area>
    </template>

    <q-scroll-area class="fit">
      <div class="q-pa-md q-gutter-sm">
        <q-tree
          :nodes="nodes"
          default-expand-all
          node-key="key"
          :loading="loading"
          @lazy-load="({ node, done }) => lazyLoad(node, done)"
        >
          <template #default-header="prop">
            <div class="row items-center">
              <div class="text-weight-bold text-primary">
                {{ prop.node.product_code }}
                <q-tooltip
                  v-if="prop.node.product_description"
                  anchor="bottom middle"
                  self="top middle"
                >
                  {{ prop.node.product_description }}
                </q-tooltip>
              </div>
            </div>
          </template>

          <template #default-body="prop">
            <div>
              <span class="text-weight-bold"
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
    </q-scroll-area>
  </q-drawer>

  <!--

  [
  {

  }
]

  -->
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

  data() {
    return {
      drawer: true,
      loading: false,
      nodes: [],
    };
  },

  created() {
    this.initData();
    this.getSerialHierarcy();
  },

  methods: {
    async lazyLoad(node, done) {
      let children = await this.getChildren(node.key);
      setTimeout(() => {
        done(children);
      }, 1000);
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

      /*this.nodes = [
        {
          label: this.serial_key,
          children: [
            { label: 'Node 1.1', lazy: true },
            { label: 'Node 1.2', lazy: true },
          ],
        },
        {
          label: 'Node 2',
          lazy: true,
        },
        {
          label: 'Lazy load empty',
          lazy: true,
        },
        {
          label: 'Node is not expandable',
          expandable: false,
          children: [{ label: 'Some node' }],
        },
      ];*/

      let children_data = await this.getChildren(this.serial_key);

      for (const parent_node of data.reverse()) {
        let node_data = [];
        let label = parent_node?.serial_code || parent_node.serial_key;
        node_data.push({
          key: parent_node.serial_key,
          label: label,
          lazy: false,
          expandable: true,
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

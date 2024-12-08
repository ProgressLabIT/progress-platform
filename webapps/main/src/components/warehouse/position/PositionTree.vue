<template>
  <div v-if="!mini_state" class="q-pa-md q-gutter-sm">
    <q-tree
      id="position-tree"
      ref="positionNodes"
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
          # {{ prop.node.label }}
          <div class="absolute-right q-py-xs">
            <q-badge v-if="prop.node.deleted" color="theme-grey" outline>
              <q-icon name="mdi-link-off" size="12px" />
            </q-badge>
          </div>
          <!--- <q-btn
            v-if="prop.node.parent_key && !prop.node.deleted && !edit_mode"
            v-show="over_key === prop.node.key"
            flat
            round
            size="xs"
            class="absolute-right"
            @click.stop="editComponentLink(prop.node)"
          >
            <q-icon name="mdi-pencil" size="xs" />
          </q-btn> -->
        </div>
      </template>
    </q-tree>
  </div>
</template>

<script>
export default {
  name: 'PositionTree',

  props: {
    mini_state: {
      type: Boolean,
      default: false,
    },
    edit_mode: {
      type: Boolean,
      default: false,
    },
    position_key: {
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
      handler(position_key) {
        if (!position_key) {
          this.selected = this.nodes[0].key;
        }
        this.$emit('select', this.selected);
      },
    },
  },

  created() {
    this.getPositionHierarcy();
    setTimeout(() => {
      if (this.$refs.positionNodes) {
        this.$refs.positionNodes.expandAll();
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

    showPositionDetails(positionKey) {
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

    getChildren(node, parent_key) {
      let child_data = [];

      for (const child_node of node) {
        child_data.push(this.convertNode(child_node, parent_key));
      }

      return child_data;
    },

    convertNode(node, parent_key) {
      let label = node?.code || node.position_key;
      let children_data = [];
      let expandable = false;
      if (node?.children) {
        children_data = this.getChildren(node.children, node.position_key);
        expandable = true;
      }
      return {
        key: node.position_key,
        parent_key: parent_key,
        label: label,
        //lazy: false,
        expandable: expandable,
        selectable: this.edit_mode ? false : true,
        children: children_data,
        deleted: node.deleted,
        product_key: node.product_key,
      };
    },

    async getPositionHierarcy() {
      this.loading = true;

      const { data } = await this.$api.get('position-hierarchy', {
        params: {
          position_key: this.position_key,
        },
      });

      this.selected = this.position_key;

      this.selected = this.position_key;

      this.nodes_data = data;

      if (!this.nodes_data.length) {
        this.$emit('noNodes', this.selected);
      }

      this.loading = false;
    },
  },
};
</script>

<style lang="sass">
#position-tree .q-tree__node-body
  padding-top: 0px !important
</style>

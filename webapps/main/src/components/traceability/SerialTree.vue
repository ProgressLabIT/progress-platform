<template>
  <div v-if="!mini_state" class="q-pa-md">
    <q-tree
      id="serial-tree"
      ref="serialNodes"
      v-model:selected="selected"
      :nodes="nodes"
      node-key="_key"
      :loading="loading"
      @lazy-load="({ node, done }) => lazyLoad(node, done)"
    >
      <template #default-header="prop">
          <div
            class="q-mr-md"
            :class="{
              'text-disabled': prop.node.replaced && prop.node._key !== selected,
              'text-weight-bold text-high': prop.node._key === selected,
              'text-low': !prop.node.replaced && prop.node._key !== selected,
            }"
            style="position: relative;"
          >
            {{ prop.node.product_code }}
          </div>
          <q-badge
            v-if="prop.node.extra_bom"
            color="low"
            outline
          >
            <q-icon name="mdi-playlist-plus" size="12px" />
          </q-badge>
          <q-badge
            v-if="prop.node.replaced"
            color="theme-grey"
            outline
          >
            <q-icon name="mdi-link-off" size="12px" />
          </q-badge>
          <q-badge
            v-if="prop.node.confirmed === false"
            color="theme-grey"
            outline
          >
            <q-icon name="mdi-cog" size="12px" />
          </q-badge>

          <!-- NODE CONTEXT MENU -->
          <q-menu v-if="canEditComponentLink(prop.node)" context-menu auto-close>
            <q-list>
              <q-item
                clickable
                @click="editComponentLink(prop.node)">
                <q-item-section>
                  <q-item-label>
                    Modifica componente
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-icon name="mdi-pencil" size="xs" />
                </q-item-section>
              </q-item>
            </q-list>
          </q-menu>

          <q-tooltip
            v-if="prop.node.product_description"
            anchor="bottom middle"
            self="top middle"
          >
            {{ prop.node.product_description }}
          </q-tooltip>
      </template>

      <template #default-body="prop">
        <div
          :class="{
            'text-theme-blue': prop.node._key === selected,
            'text-disabled': prop.node.replaced,
          }"
        >
          # {{ prop.node.code }}
        </div>
      </template>
    </q-tree>
  </div>
</template>

<script setup>
import { Dialog } from 'quasar'
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { api } from '@/boot/axios'
import SerialComponentLinkEditDialog from '@/components/traceability/SerialComponentLinkEditDialog.vue'
import { sendEvent } from '@/composables/event'

const props = defineProps({
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
})

const emit = defineEmits(['select', 'noNodes'])

const store = useStore()
const loading = ref(false)
const selected = ref(null)
const nodes_data = ref([])
const serialNodes = ref(null)


const nodes = computed(() => nodes_data.value.map((n) => convertNode(n, undefined)))

getSerialHierarcy()
setTimeout(() => {
  if (serialNodes.value) {
    serialNodes.value.expandAll()
  }
}, 500)

watch(selected, (newSerial, oldSerial) => {
  if (!newSerial) {
    selected.value = nodes.value[0]._key
    return
  }

  // Only emit if this isn't the initial selection (oldSerial was null)
  if (oldSerial !== null && oldSerial !== newSerial) {
    emit('select', selected.value)
  }
})

async function lazyLoad(node, done) {
  let children = await getChildren(node.key)
  setTimeout(() => {
    done(children)
  }, 1000)
}

function getChildren(node, parent_key) {
  let child_data = []

  for (const child_node of node) {
    child_data.push(convertNode(child_node, parent_key))
  }

  return child_data
}

function convertNode(node, parent_key) {
  let children_data = []
  let expandable = false
  if (node?.children) {
    children_data = getChildren(node.children, node.serial_key)
    expandable = true
  }
  return {
    _key: node.serial_key,
    parent_key: parent_key,
    code: node.serial_code,
    lazy: false,
    expandable: expandable,
    selectable: props.edit_mode ? false : true,
    children: children_data,
    replaced: node.replaced,
    confirmed: node.confirmed,
    extra_bom: node.extra_bom,
    product_key: node.product_key,
    product_code: node.product_code,
    product_description: node.product_description,
  }
}

async function getSerialHierarcy() {
  loading.value = true

  const { data } = await api.get('serial-hierarchy', {
    params: {
      serial_key: props.serial_key,
    },
  })

  selected.value = props.serial_key
  nodes_data.value = data

  if (!nodes_data.value.length) {
    emit('noNodes', selected.value)
  }

  loading.value = false
}

function canEditComponentLink(node) {
  // Do not allow to edit component link if the serial is not confirmed or replaced or is the root node
  return node.confirmed !== false && node.replaced !== true && node.parent_key
}

function editComponentLink(node) {
  const promises = [
    store.dispatch('appendSerial', { serial_key: node.parent_key }),
  ]
  if (node._key) {
    promises.push(store.dispatch('appendSerial', { serial_key: node._key }))
  }
  Promise.all(promises).then((values) => {
    showEditComponentLink(node, values[0])
  })
}

function showEditComponentLink(node, parentSerial) {
  let serialModel = {
    _key: node._key,
    code: node.code,
    product_key: node.product_key,
    wo_key: parentSerial.wo_key,
    reason: '',
  }

  Dialog.create({
    component: SerialComponentLinkEditDialog,
    componentProps: {
      node: node,
      serial: serialModel,
    },
  }).onOk((newValues) => {
    saveNewComponentLink(node, newValues)
  })
}

async function saveNewComponentLink(node, newSerial) {
  const sharedEventData = {
    component_key: node.product_key,
    parent_serial_key: node.parent_key,
  }

  if (node._key) {
    await sendEvent({
      event_type: 'SERIAL_UNLINKED',
      event_data: {
        ...sharedEventData,
        child_serial_key: node._key,
        reason: newSerial.reason,
        process_inventory: newSerial.processInventory.oldLink,
      },
    })
  }

  if (newSerial._key) {
    const event_data = {
      ...sharedEventData,
      child_serial_key: newSerial._key,
      reason: newSerial.reason,
      process_inventory: newSerial.processInventory.newLink,
    }

    if (newSerial.used) {
      event_data.replace_existing = true
    }

    if (!newSerial.available) {
      event_data.process_inventory = false
    }

    await sendEvent({
      event_type: 'SERIAL_LINKED',
      event_data,
    })
  }

  nodes_data.value = []
  getSerialHierarcy()
  setTimeout(() => {
    if (serialNodes.value) {
      serialNodes.value.expandAll()
    }
  }, 500)
}
</script>

<style lang="sass">
#serial-tree .q-tree__node-body
  padding-top: 0px !important
</style>

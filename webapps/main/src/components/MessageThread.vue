<template>
  <div class="col column q-pa-md full-height">
    <slot name="header"></slot>

    <div class="col scroll q-py-md">
      <MessageEntry
        v-for="m in messages"
        :key="m._key"
        :message="m"
        @change="getMessages"
      />
    </div>

    <div class="col-auto">
      <q-separator spaced></q-separator>
      <div class="row justify-between items-center">
        <div class="col">
          <q-input
            v-model="new_message"
            filled
            autogrow
            :placeholder="$t('message_prompt')"
          >
            <template #append>
              <q-btn
                v-if="new_message.length"
                round
                icon="mdi-send"
                :loading="loading"
                color="theme-blue"
                size="12px"
                @click="postMessage"
              >
              </q-btn>
            </template>
          </q-input>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { useStore } from 'vuex';
import { api } from '@/boot/axios.js';
import MessageEntry from '@/components/MessageEntry.vue';
import { sendEvent } from '@/composables/event.js';
import { useSSE } from '@/composables/useSSE';

const props = defineProps({
  context: {
    type: String,
    required: true
  },
  context_key: {
    type: String,
    default: undefined,
  },
});

const store = useStore();

// Reactive data
const recipient_prefix_map = ref({
  issue: 'Issue/',
  work_order: 'WorkOrder/',
  serial: 'Serial/',
  task: 'Task/',
});
const messages = ref([]);
const new_message = ref('');
const { subscribe: subscribeSSE } = useSSE('global-notification');
const loading = ref(false);

// Computed properties
const recipient_id = computed(() => {
  if (!props.context) {
    return;
  }
  if (props.context === 'job') {
    return (
      'WorkOrder/' + store.state.traceability.working_job_data.wo_key
    );
  } else {
    return recipient_prefix_map.value[props.context] + props.context_key;
  }
});

// Methods
function handleMessage(message) {
  let event = JSON.parse(message.data);
  if (event.notification === 'REFRESH') {
    getMessages();
  }
}

function getMessages() {
  api
    .get('message', { params: { recipient_id: recipient_id.value } })
    .then((resp) => (messages.value = resp.data));
}

async function postMessage() {
  const message_data = {
    sender: `User/${store.state.session.user._key}`,
    recipient: recipient_id.value,
    content: new_message.value,
  };
  loading.value = true;

  try {
    await sendEvent({
      event_type: 'MESSAGE_POSTED',
      event_data: { ...message_data },
    });
    getMessages();
    new_message.value = '';
  } finally {
    loading.value = false;
  }
}

// Watchers
watch(() => props.context_key, () => {
  getMessages();
});

// Lifecycle
onMounted(() => {
  loading.value = true;
  store.dispatch('loadUsers');
  loading.value = false;

  getMessages();
  subscribeSSE((event) => {
    handleMessage(event);
  });
});
</script>

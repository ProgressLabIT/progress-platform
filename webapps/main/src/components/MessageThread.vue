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

<script>
import MessageEntry from '@/components/MessageEntry.vue';
import event from '@/mixins/event.js';

export default {
  name: 'MessageThread',

  components: {
    MessageEntry,
  },

  mixins: [event],

  props: {
    context: {
      type: String,
      required: true,
      validator: (value) => ['issue', 'work_order', 'job'].includes(value),
    },
    context_key: {
      type: String,
      default: undefined,
    },
  },

  data() {
    return {
      recipient_prefix_map: {
        issue: 'Issue/',
        work_order: 'WorkOrder/',
      },
      messages: [],
      new_message: '',
      polling_instance: null,
    };
  },

  computed: {
    recipient_id() {
      if (this.context === 'job') {
        return (
          'WorkOrder/' + this.$store.state.traceability.working_job_data.wo_key
        );
      } else {
        return this.recipient_prefix_map[this.context] + this.context_key;
      }
    },
  },
  created() {
    this.$store.dispatch('loadUsers');
  },

  mounted() {
    this.getMessages();
    this.polling_instance = setInterval(this.getMessages, 10000);
  },
  unmounted() {
    clearInterval(this.polling_instance);
  },

  methods: {
    getMessages() {
      this.$api
        .get('message', { params: { recipient_id: this.recipient_id } })
        .then((resp) => (this.messages = resp.data));
    },

    postMessage() {
      const message_data = {
        sender: `User/${this.$store.state.session.user._key}`,
        recipient: this.recipient_id,
        content: this.new_message,
      };
      this.loading = true;
      this.sendEvent({
        event_type: 'MESSAGE_POSTED',
        event_data: { message_data },
      }).then(() => {
        this.getMessages();
        this.new_message = '';
        this.loading = false;
      });
    },
  },
};
</script>

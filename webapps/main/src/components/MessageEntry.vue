<template>
  <div class="q-mb-md">
    <div class="row items-start">
      <q-card square bordered flat class="surface2 q-pa-sm col q-mr-md">
        <div class="weight-bold text-italic q-mb-sm">
          {{ sender.name }} {{ sender.surname }}
        </div>
        <div v-if="message.deleted" class="text-italic text-theme-grey">
          {{ $t('deleted') }}
        </div>
        <div v-else style="white-space: pre-line">
          {{ message.content }}
        </div>
        <div
          v-if="
            sender_key === $store.state.session.user._key && !message.deleted
          "
          class="absolute-top-right q-mt-xs q-mr-xs"
        >
          <q-btn round dense size="xs" flat icon="mdi-dots-horizontal">
            <q-popup-proxy style="min-width: 150px" auto-close>
              <q-list>
                <q-item v-ripple clickable @click="show_update_prompt = true">
                  <q-item-section avatar>
                    <q-icon name="mdi-pencil" size="xs" />
                  </q-item-section>
                  <q-item-section>
                    {{ $capitalize($t('edit')) }}
                  </q-item-section>
                </q-item>
                <q-item v-ripple clickable @click="show_delete = true">
                  <q-item-section avatar>
                    <q-icon name="mdi-delete" size="xs" />
                  </q-item-section>
                  <q-item-section>
                    {{ $capitalize($t('delete')) }}
                  </q-item-section>
                </q-item>
              </q-list>
            </q-popup-proxy>
          </q-btn>
        </div>

        <div
          v-if="show_delete"
          class="absolute-full surface2 row items-center justify-between q-px-lg"
        >
          <div class="display highlight">
            {{ $t('confirm_question') }}
          </div>
          <div>
            <q-btn
              round
              size="sm"
              color="theme-red"
              icon="mdi-delete"
              class="q-mr-sm"
              @click="deleteMessage"
            >
            </q-btn>
            <q-btn
              round
              size="sm"
              color="theme-grey"
              icon="mdi-close"
              @click="show_delete = false"
            >
            </q-btn>
          </div>
        </div>
      </q-card>
      <BaseUserAvatar :user="sender" name_class="text-low" :show_name="false" />
    </div>
    <div class="text-italic text-low smaller q-mt-sm">
      {{ datetime }}
    </div>

    <BasePrompt
      :show="show_update_prompt"
      :initial_value="message.content"
      input_type="textarea"
      @update="updateMessage"
      @close="show_update_prompt = false"
    >
    </BasePrompt>
  </div>
</template>

<script>
import BasePrompt from '@/components/BasePrompt.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import event from '@/mixins/event.js';

export default {
  name: 'MessageEntry',

  components: {
    BaseUserAvatar,
    BasePrompt,
  },

  mixins: [event],

  props: {
    message: {
      type: Object,
      required: true,
    },
  },

  emits: ['change'],

  data() {
    return {
      show_update_prompt: false,
      show_delete: false,
    };
  },

  computed: {
    sender_key() {
      return this.message._from.split('/')[1];
    },

    sender() {
      return this.$store.getters.user_data(this.sender_key);
    },

    datetime() {
      const config = {
        year: '2-digit',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit',
        weekday: 'short',
      };
      return this.$capitalize(
        this.$formatDateTime(this.message.created, this.$i18n.locale, config),
      );
    },
  },

  methods: {
    updateMessage(content) {
      const message_data = {
        ...this.message,
        content,
      };
      this.sendEvent({
        event_type: 'MESSAGE_UPDATED',
        event_data: { message_data },
      }).then(() => {
        this.$emit('change');
      });
      this.show_update_prompt = false;
    },

    deleteMessage() {
      this.sendEvent({
        event_type: 'MESSAGE_DELETED',
        event_data: {
          message_data: { ...this.message },
        },
      }).then(() => {
        this.$emit('change');
        this.show_delete = false;
      });
    },
  },
};
</script>

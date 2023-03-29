<template>
  <BaseDialog :show="true" @close="exit" maximized>
    <q-card class="surface1 row" bordered square style="width: 90vw; height: 90vh">

      <!-- LEFT SECTION -->
      <div class="col-8 column full-height">
        <IssueHeader :issue="issue" @type-change="refreshIssue"/>
        <q-list class="q-ml-lg q-px-xl col scroll q-pb-lg">
          <q-item
            v-for="e, index in history"
            :key="e._key"
            class="q-mt-md relative-position row justify-between full-width items-baseline">

            <!-- TIMELINE DOT & LINE -->
            <div style="position: absolute; left: -30px; top: 13px; height: 100%; width: 32px">
              <div class="column full-height">
                <div class="dot"></div>
                <div v-if="index < history.length - 1" class="thread"></div>
              </div>
            </div>

            <!-- EVENT TYPE -->
            <q-item-section class="text-italic">
              {{ $formatDateTime(e.timestamp, $i18n.locale, 'DATETIME_MED') }}
            </q-item-section>
            <q-item-section class="text-h4 highlight text-uppercase">
              {{ $t(`events.${e.event_type}`) }}
            </q-item-section>
            <q-space />
            <q-item-section>
              <BaseUserAvatar name_first :user="getUserData(e)" />
            </q-item-section>
          </q-item>
        </q-list>

        <q-space />

        <!-- ACTIONS -->
        <div class="row q-pa-md q-gutter-lg">
          <template v-if="issue.open">
            <q-btn
              color="theme-blue"
              :label="$t('issue_button_close')"
              @click="closeIssue">
            </q-btn>
            <q-btn
              v-if="issue.critical"
              color="theme-blue"
              :label="$t('issue_button_remove_critical')"
              @click="toggleCritical">
            </q-btn>
            <q-btn
              v-else
              color="theme-red"
              :label="$t('issue_button_add_critical')"
              @click="toggleCritical">
            </q-btn>
          </template>
          <template v-else>
            <q-btn
              color="theme-blue"
              :label="$t('issue_button_reopen')"
              @click="() => { critical=false; reopenIssue() }">
            </q-btn>
            <q-btn
              color="theme-red"
              :label="$t('issue_button_reopen_critical')"
              @click="() => { critical=true; reopenIssue() }">
            </q-btn>
          </template>
          <q-space />
          <q-btn
            color="theme-grey"
            :label="$t('back')"
            @click="$router.back()">
          </q-btn>
        </div>
      </div>


      <q-separator vertical spaced />

      <!-- RIGHT SECTION -->
      <div class="col column q-pa-md full-height">
        <div class="display low-text text-h5 col-auto q-pb-md">
          {{ $t('message', 2) }}
        </div>
        <q-separator></q-separator>
        <div class="col scroll q-py-md">
          <Message v-for="m in messages" :key="m._key" :message="m" />
        </div>
        <div class="col-auto">
          <q-separator spaced></q-separator>
          <div class="row justify-between items-center">
            <div class="col">
              <q-input
                v-if="!recording"
                filled
                autogrow
                v-model="new_message"
                :placeholder="$t('message_prompt')">
              </q-input>
            </div>
          </div>
          <q-btn
            class="full-width q-mt-md"
            :loading="loading"
            color="theme-blue"
            :label="$t('send')"
            @click="postMessage">
          </q-btn>
        </div>
      </div>
    </q-card>
  </BaseDialog>
</template>

<script>
import event from '@/mixins/event.js'
import IssueHeader from '@/components/IssueHeader.vue'
import enrichIssue from '@/mixins/issues.js'
import Message from '@/components/Message.vue'
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'
import BaseDialog from '@/components/BaseDialog.vue'
export default {

  name: 'IssueDetail',

  components: {
    IssueHeader,
    Message,
    BaseUserAvatar,
    BaseDialog
  },

  mixins: [enrichIssue, event],

  props: {
    // from router
    issue_key: {
      type: String,
      required: true
    },
    job_key: String,
    wo_key: String
  },

  data() {
    return {
      messages: [],
      history: [],
      new_message: '',
      loading: false,
      recording: false,
      base_path: '/media/user/',
    }
  },

  computed: {
    issue() {
      const issue_data = this.$store.getters.getIssueData(this.issue_key)
      return this.enrichIssue(issue_data)
    },

    context() {
      // Check where the component is being used
      return this.job_key
        ? 'job'
        : this.wo_key
        ? 'work-order'
        : undefined
    },

    fetch_filter() {
      return this.context == 'job' ? { job_key: this.job_key }
        : this.context == 'work-order' ? { work_order_key: this.wo_key }
        : null
    }
  },

  methods: {
    getMessages() {
      this.$api.get('message', { params: { issue_key: this.issue._key }})
      .then(resp => this.messages = resp.data)
    },

    getHistory() {
      this.$api.get('event', { params: { issue_key: this.issue._key }})
      .then(resp => this.history = resp.data)
    },

    getAvatarSrc(user) {
      return this.base_path + (user.name + user.surname).replace(/\s+/g, '') + '.jpg'
    },

    getUserData(event) {
      const user = this.$store.getters.user_data(event.user_key)
      return {
        ...user,
        full_name: user.name + ' ' + user.surname,
        src: this.getAvatarSrc(user)
      }
    },

    notifyUpdate({ message, color='theme-green' }) {
      this.$q.notify({
        message: this.$t('issue_updated'),
        color: 'theme-green',
        timeout: '1500',
        position: 'top'
      })
    },

    refreshIssue() {
      this.$store.dispatch('getIssues', this.fetch_filter)
      this.getHistory()
    },

    closeIssue() {
      this.sendEvent({
        event_type: 'ISSUE_CLOSED',
        event_data: {
          issue_data: {
            _key: this.issue._key
          }
        }
      }).then(() => {
        this.refreshIssue()
        this.notifyUpdate({ message: this.$t('issue_updated') })
      })
    },

    toggleCritical() {
      this.issue.critical = !this.issue.critical
      this.sendEvent({
        event_type: 'ISSUE_UPDATED',
        event_data: {
          issue_data: {
            _key: this.issue._key,
            critical: this.issue.critical
          }
        }
      }).then(() => {
        this.refreshIssue()
        this.notifyUpdate({
          message: this.$t('issue_updated'),
          color: this.issue.critical ? 'theme-red' : 'theme-green'
        })
      })
    },

    reopenIssue() {
      this.sendEvent({
        event_type: 'ISSUE_REOPENED',
        event_data: {
          issue_data: {
            _key: this.issue._key,
            critical: this.issue.critical,
          }
        }
      }).then(() => {
        this.refreshIssue()
        this.notifyUpdate({
          message: this.$t('issue_updated')
        })
      })
    },

    postMessage() {
      const message_data = {
        sender: `User/${this.$store.state.session.user._key}`,
        recipient: `Issue/${this.issue._key}`,
        content: this.new_message
      }
      this.loading = true
      this.sendEvent({
        event_type: 'MESSAGE_POSTED',
        event_data: { message_data }
      }).then(() => {
        this.new_message = ''
        this.getMessages()
        this.getHistory()
        this.loading = false
      })
    }
  },

  created() {
    this.$store.dispatch('loadUsers')
    this.$store.dispatch('getIssues', this.fetch_filter)
    this.getMessages()
    this.getHistory()
  }
}
</script>

<style lang="sass" scoped>
.dot
  height: 13px
  width: 13px
  border-radius: 100%
  background-color: #888
  border: 5px solid var(--surface-1)
  box-sizing: content-box
  z-index:99

.thread
  position: absolute
  height: 100%
  left: 11px
  top: 20px
  width: 1px
  background-color: #fff3
</style>

<template>
  <BaseDialog :show="true" @close="exit" maximized>
    <q-card class="surface1 row" bordered square style="width: 95vw; height: 95vh">

      <!-- LEFT SECTION -->
      <div class="col-7 column full-height">

        <!-- HEADER -->
        <IssueHeader :issue="issue" @type-change="refreshIssue"/>


        <!-- FORM DATA -->
        <div class="row items-center q-pl-lg q-mt-sm">
          <div class="col-auto text-h5 weight bold text-uppercase text-low">
            {{ $t('form_title') }}
          </div>
          <div class="col">
            <q-separator inset />
          </div>
        </div>

        <div class="row q-px-lg q-pt-md q-mb-md">
          <template v-if="issue.data.length > 0">
            <div v-for="field in issue.data" :key="field._key" class="col-auto q-pr-md">
              <FormField
                :field="field"
                :root-path="`/media/issue/${issue_key}`"
                dense
                disable
              />
            </div>
          </template>
          <div v-else class="col-auto text-italic">
            No data
          </div>
        </div>

        <!-- ISSUE EVENTS -->
        <div class="row items-center q-pl-lg">
          <div class="col-auto text-h5 weight bold text-uppercase text-low">
            {{ $t('history') }}
          </div>
          <div class="col">
            <q-separator inset />
          </div>
        </div>


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
              {{ getHumanDate(e.timestamp) }}
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
              size="12px"
              icon="mdi-check"
              :label="$t('issue_button_close')"
              @click="closeIssue">
            </q-btn>
            <q-btn
              v-if="issue.critical"
              size="12px"
              icon="mdi-alert-circle-outline"
              color="theme-blue"
              :label="$t('issue_button_remove_critical')"
              @click="toggleCritical">
            </q-btn>
            <q-btn
              v-else
              size="12px"
              color="theme-red"
              icon="mdi-alert-octagon"
              :label="$t('issue_button_add_critical')"
              @click="toggleCritical">
            </q-btn>
          </template>
          <template v-else>
            <q-btn
              size="12px"
              color="theme-blue"
              icon="mdi-restore"
              :label="$t('issue_button_reopen')"
              @click="() => { issue.critical=false; reopenIssue() }">
            </q-btn>
            <q-btn
              color="theme-red"
              size="12px"
              icon="mdi-restore-alert"
              :label="$t('issue_button_reopen_critical')"
              @click="() => { issue.critical=true; reopenIssue() }">
            </q-btn>
          </template>
          <q-space />
          <q-btn
            v-if="user_can_delete"
            color="theme-red"
            size="12px"
            icon="mdi-delete"
            :label="$t('delete')"
            @click="deleteIssue">
          </q-btn>
          <q-btn
            size="12px"
            icon="mdi-keyboard-return"
            color="theme-grey"
            :label="$t('back')"
            @click="exit">
          </q-btn>
        </div>
      </div>


      <q-separator vertical spaced />

      <!-- RIGHT SECTION -->
      <MessageThread
        :messages="messages"
        context="issue"
        :context_key="issue._key">
        <template #header>
          <div class="display low-text text-h5 col-auto q-pb-md">
            {{ $t('message', 2) }}
          </div>
          <q-separator></q-separator>
        </template>
      </MessageThread>

    </q-card>
  </BaseDialog>
</template>

<script>
import event from '@/mixins/event.js'
import IssueHeader from '@/components/IssueHeader.vue'
import enrichIssue from '@/mixins/issues.js'
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'
import BaseDialog from '@/components/BaseDialog.vue'
import FormField from '@/components/FormField.vue'
import MessageThread from '@/components/MessageThread.vue'


export default {

  name: 'IssueDetail',

  components: {
    IssueHeader,
    MessageThread,
    BaseUserAvatar,
    BaseDialog,
    FormField
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

    issue_type() {
      return this.$store.getters.getIssueType(this.issue.issue_type_key)
    },

    form_fields() {
      const form_template = this.issue_type?.form_template ?? []
      return form_template.map(field => ({
        ...field,
        value: this.issue.data
          .find(({ _key }) => _key === field._key)?.value
      }))
    },

    user_can_delete() {
      return this.$store.getters.hasPermission('production')
    }
  },

  methods: {
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

    getHumanDate(timestamp) {
      const config = {
        year: '2-digit',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit',
        weekday: 'short'
      }
      return this.$capitalize(this.$formatDateTime(timestamp, this.$i18n.locale, config))
    },

    notify({ message, color='theme-green' }) {
      this.$q.notify({
        message,
        color,
        timeout: '1500',
        position: 'top'
      })
    },

    refreshIssue() {
      this.$store.dispatch('getIssues', { issue_key: this.issue_key })
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
        this.notify({ message: this.$t('issue_update_success') })
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
        this.notify({
          message: this.$t('issue_update_success'),
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
        this.notify({
          message: this.$t('issue_updated')
        })
      })
    },

    deleteIssue() {
      this.$q.dialog({
        cancel: true,
        title: this.$t('issue_delete_confirm_title'),
        message: this.$t('issue_delete_confirm_question')
      }).onOk(() => {
        this.sendEvent({
          event_type: 'ISSUE_DELETED',
          event_data: {
            issue_data: {
              _key: this.issue_key
            }
          }
        }).then(async () => {
          const work_order_key = this.$store.state.traceability.working_job_data.wo_key
          await this.$store.dispatch('getIssues', { work_order_key })
          this.exit()
          this.notify({
            message: this.$t('issue_delete_success')
          })
        })
      })
    },

    exit() {
      this.$router.back()
    }
  },

  created() {
    this.$store.dispatch('loadUsers')
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

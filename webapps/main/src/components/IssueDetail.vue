<template>
  <BaseDialog :show="true" maximized @close.stop="exit">
    <q-card
      class="surface1 row q-px-sm"
      bordered
      square
      style="width: 95vw; height: 95vh"
    >
    <q-splitter
      v-model="dataColumnWidth"
      class="fit"
      separator-class="text-disabled">

      <template #before>
      <!-- LEFT SECTION -->
      <div class="column full-height q-px-md">
        <!-- HEADER -->
        <IssueHeader :issue="issue" @type-change="refreshIssue" />


        <q-tabs
          v-model="tab"
          dense
          class="q-mt-md text-low"
          content-class="text-h5"
          indicator-color="theme-blue"
          align="left"
          active-class="text-high weight-bold"
        >
          <q-tab name="form" :label="$t('form_title')" class="text-left" />
          <q-tab name="history" :label="$t('history')" />
          <q-tab name="links" :label="$t('link', 2)" />
        </q-tabs>

        <q-card square class="col surface2 scroll">
          <q-tab-panels v-model="tab" class="transparent">
            <!-- FORM DATA -->
            <q-tab-panel name="form">
              <div v-if="issue.data.length > 0" class="column q-gutter-md">
                <div
                  v-for="field in issue.data"
                  :key="field._key"
                  class="col-auto q-pr-md"
                >
                  <FormField
                    :field="field"
                    :root-path="`${root_path}/${field._key}`"
                    dense
                    disable
                  />
                </div>
              </div>
              <div v-else class="col-auto text-italic">
                No data
              </div>
            </q-tab-panel>

            <!-- ISSUE EVENTS -->
            <q-tab-panel name="history">
              <q-list class="q-ml-lg q-px-xl col scroll q-pb-lg">
                <q-item
                  v-for="(e, index) in history"
                  :key="e._key"
                  class="q-mt-md relative-position row justify-between full-width items-baseline"
                >
                  <!-- TIMELINE DOT & LINE -->
                  <div
                    style="
                      position: absolute;
                      left: -30px;
                      top: 13px;
                      height: 100%;
                      width: 32px;
                    "
                  >
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
            </q-tab-panel>

            <!-- ISSUE LINKS -->
            <q-tab-panel name="links">
              <q-list>
                <q-item v-for="[link, value] in Object.entries(issue.links)" :key="link">
                  <q-item-section class="text-h5 text-uppercase col-4">
                    {{ $t(linkTypes[link].label) }}
                  </q-item-section>
                  <q-item-section class="text-body2">
                    {{ value?.[linkTypes[link].prop] ?? '-' }}
                  </q-item-section>
                </q-item>
              </q-list>
            </q-tab-panel>

          </q-tab-panels>

      </q-card>


        <!-- ACTIONS -->
        <div class="row q-pa-md q-gutter-lg">
          <template v-if="issue.open">
            <q-btn
              color="theme-blue"
              size="12px"
              icon="mdi-check"
              :label="$t('issue_button_close')"
              @click="closeIssue"
            >
            </q-btn>
            <q-btn
              v-if="issue.critical"
              size="12px"
              icon="mdi-alert-circle-outline"
              color="theme-blue"
              :label="$t('issue_button_remove_critical')"
              @click="toggleCritical"
            >
            </q-btn>
            <q-btn
              v-else
              size="12px"
              color="theme-red"
              icon="mdi-alert-octagon"
              :label="$t('issue_button_add_critical')"
              @click="toggleCritical"
            >
            </q-btn>
          </template>
          <template v-else>
            <q-btn
              size="12px"
              color="theme-blue"
              icon="mdi-restore"
              :label="$t('issue_button_reopen')"
              @click="
                () => {
                  issue.critical = false;
                  reopenIssue();
                }
              "
            >
            </q-btn>
            <q-btn
              color="theme-red"
              size="12px"
              icon="mdi-restore-alert"
              :label="$t('issue_button_reopen_critical')"
              @click="
                () => {
                  issue.critical = true;
                  reopenIssue();
                }
              "
            >
            </q-btn>
          </template>
          <q-space />
          <q-btn
            v-if="user_can_delete"
            color="theme-red"
            size="12px"
            icon="mdi-delete"
            :label="$t('delete')"
            @click="deleteIssue"
          >
          </q-btn>
          <q-btn
            size="12px"
            icon="mdi-keyboard-return"
            color="theme-grey"
            :label="$t('back')"
            @click="exit"
          >
          </q-btn>
        </div>
      </div>

    </template>
    <template #after>

      <!-- RIGHT SECTION -->
      <MessageThread
        :messages="messages"
        context="issue"
        :context_key="issue._key"
      >
        <template #header>
          <div class="display low-text text-h5 col-auto q-pb-md">
            {{ $t('message', 2) }}
          </div>
          <q-separator></q-separator>
        </template>
      </MessageThread>
    </template>
    </q-splitter>

    </q-card>
  </BaseDialog>
</template>

<script>
import BaseDialog from '@/components/BaseDialog.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import FormField from '@/components/FormField.vue';
import IssueHeader from '@/components/IssueHeader.vue';
import MessageThread from '@/components/MessageThread.vue';
import event from '@/mixins/event.js';
import enrichIssue from '@/mixins/issues.js';

export default {
  name: 'IssueDetail',

  components: {
    IssueHeader,
    MessageThread,
    BaseUserAvatar,
    BaseDialog,
    FormField,
  },

  mixins: [enrichIssue, event],

  props: {
    // from router
    issueKey: {
      type: String,
      required: true,
    },
  },

  data() {
    return {
      messages: [],
      history: [],
      loading: false,
      recording: false,
      base_path: '/media/user/',
      tab: 'form',
      dataColumnWidth: 70,
      linkTypes: {
        job: {
          label: 'job.label',
          prop: '_key'
        },
        product: {
          prop: 'code',
          label: 'product.label'
        },
        phase: {
          prop: 'alias',
          label: 'phase.phase'
        },
        work_order: {
          prop: 'wo_code',
          label: 'work_order.long'
        },
        serial: {
          prop: 'code',
          label: 'serial',
        },
        user: {
          prop: 'username',
          label: 'user.label'
        },
        'operation': {
          prop: 'name',
          label: 'operation.label'
        }
      }
    };
  },

  computed: {
    issue() {
      const issue_data = this.$store.getters.getIssueData(this.issueKey);
      return this.enrichIssue(issue_data);
    },

    issue_type() {
      return this.$store.getters.getIssueType(this.issue.issue_type_key);
    },

    form_fields() {
      const form_template = this.issue_type?.form_template ?? [];
      return form_template.map((field) => ({
        ...field,
        value: this.issue.data.find(
          ({ form_field_key }) => form_field_key === field._key,
        )?.value,
      }));
    },

    root_path() {
      return '/media/issue/' + this.issueKey;
    },

    user_can_delete() {
      return this.$store.getters.hasPermission('production');
    },
  },

  created() {
    this.$store.dispatch('loadUsers');
    this.getHistory();
  },

  methods: {
    getHistory() {
      this.$api
        .get('event', { params: { issue_key: this.issue._key } })
        .then((resp) => (this.history = resp.data));
    },

    getAvatarSrc(user) {
      return (
        this.base_path + (user.name + user.surname).replace(/\s+/g, '') + '.jpg'
      );
    },

    getUserData(event) {
      const user = this.$store.getters.user_data(event.user_key);
      return {
        ...user,
        full_name: user.name + ' ' + user.surname,
        src: this.getAvatarSrc(user),
      };
    },

    getHumanDate(timestamp) {
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
        this.$formatDateTime(timestamp, this.$i18n.locale, config),
      );
    },

    notify({ message, color = 'theme-green' }) {
      this.$q.notify({
        message,
        color,
        timeout: '1500',
        position: 'top',
      });
    },

    refreshIssue() {
      this.$store.dispatch('getIssues', { issue_key: this.issueKey });
      this.getHistory();
    },

    closeIssue() {
      this.sendEvent({
        event_type: 'ISSUE_CLOSED',
        event_data: {
          issue_data: {
            _key: this.issue._key,
          },
        },
      }).then(() => {
        this.refreshIssue();
        this.notify({ message: this.$t('issue_update_success') });
      });
    },

    toggleCritical() {
      this.issue.critical = !this.issue.critical;
      this.sendEvent({
        event_type: 'ISSUE_UPDATED',
        event_data: {
          issue_data: {
            _key: this.issue._key,
            critical: this.issue.critical,
          },
        },
      }).then(() => {
        this.refreshIssue();
        this.notify({
          message: this.$t('issue_update_success'),
          color: this.issue.critical ? 'theme-red' : 'theme-green',
        });
      });
    },

    reopenIssue() {
      this.sendEvent({
        event_type: 'ISSUE_REOPENED',
        event_data: {
          issue_data: {
            _key: this.issue._key,
            critical: this.issue.critical,
          },
        },
      }).then(() => {
        this.refreshIssue();
        this.notify({
          message: this.$t('issue_updated'),
        });
      });
    },

    deleteIssue() {
      this.$q
        .dialog({
          cancel: true,
          title: this.$t('issue_delete_confirm_title'),
          message: this.$t('issue_delete_confirm_question'),
        })
        .onOk(() => {
          this.sendEvent({
            event_type: 'ISSUE_DELETED',
            event_data: {
              issue_data: {
                _key: this.issueKey,
              },
            },
          }).then(async () => {
            const work_order_key =
              this.$store.state.traceability.working_job_data.wo_key;
            await this.$store.dispatch('getIssues', { work_order_key });
            this.exit();
            this.notify({
              message: this.$t('issue_delete_success'),
            });
          });
        });
    },

    exit() {
      this.$router.back();
    },
  },
};
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

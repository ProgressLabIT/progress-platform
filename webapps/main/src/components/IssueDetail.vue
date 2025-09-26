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
              <q-list class="col q-pb-lg">
                <TimelineItem
                  v-for="(e, index) in history"
                  :key="e._key"
                  :event="e"
                  :show-thread="index < history.length - 1"
                  :user-data="getUserData(e)"
                />
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

<script setup>
import { useQuasar } from 'quasar';
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';
import { api } from '@/boot/axios.js';
import BaseDialog from '@/components/BaseDialog.vue';
import FormField from '@/components/FormField.vue';
import IssueHeader from '@/components/IssueHeader.vue';
import MessageThread from '@/components/MessageThread.vue';
import TimelineItem from '@/components/TimelineItem.vue';
import { sendEvent } from '@/composables/event.js';

const props = defineProps({
  // from router
  issueKey: {
    type: String,
    required: true,
  },
});

// Composables
const store = useStore();
const { t } = useI18n();
const $q = useQuasar();
const router = useRouter();

// Reactive data
const messages = ref([]);
const history = ref([]);
const base_path = ref('/media/user/');
const tab = ref('form');
const dataColumnWidth = ref(70);
const linkTypes = ref({
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
});

// Helper function (from enrichIssue mixin)
function enrichIssue(i) {
  // Add badge data for visual indication of status
  let badge = !i.open
    ? { color: 'theme-grey', text: t('closed') }
    : i.critical
      ? { color: 'theme-red', text: t('critical') }
      : { color: 'theme-blue', text: t('open') };
  return { ...i, badge };
}

// Computed properties
const issue = computed(() => {
  const issue_data = store.getters.getIssueData(props.issueKey);
  return enrichIssue(issue_data);
});

const root_path = computed(() => '/media/issue/' + props.issueKey);

const user_can_delete = computed(() => store.getters.hasPermission('production'));

// Methods
function getHistory() {
  api
    .get('event', { params: { issue_key: issue.value._key } })
    .then((resp) => (history.value = resp.data));
}

function getAvatarSrc(user) {
  return (
    base_path.value + (user.name + user.surname).replace(/\s+/g, '') + '.jpg'
  );
}

function getUserData(event) {
  const user = store.getters.user_data(event.user_key);
  return {
    ...user,
    full_name: user.name + ' ' + user.surname,
    src: getAvatarSrc(user),
  };
}

function notify({ message, color = 'theme-green' }) {
  $q.notify({
    message,
    color,
    timeout: 1500,
    position: 'top',
  });
}

function refreshIssue() {
  store.dispatch('refreshIssueData', props.issueKey);
  getHistory();
}

async function closeIssue() {
  try {
    await sendEvent({
      event_type: 'ISSUE_CLOSED',
      event_data: {
        issue_data: {
          _key: issue.value._key,
        },
      },
    });
    refreshIssue();
    notify({ message: t('issue_update_success') });
  } catch (error) {
    console.error('Error closing issue:', error);
  }
}

async function toggleCritical() {
  issue.value.critical = !issue.value.critical;
  try {
    await sendEvent({
      event_type: 'ISSUE_UPDATED',
      event_data: {
        issue_data: {
          _key: issue.value._key,
          critical: issue.value.critical,
        },
      },
    });
    refreshIssue();
    notify({
      message: t('issue_update_success'),
      color: issue.value.critical ? 'theme-red' : 'theme-green',
    });
  } catch (error) {
    console.error('Error updating issue critical status:', error);
  }
}

async function reopenIssue() {
  try {
    await sendEvent({
      event_type: 'ISSUE_REOPENED',
      event_data: {
        issue_data: {
          _key: issue.value._key,
          critical: issue.value.critical,
        },
      },
    });
    refreshIssue();
    notify({
      message: t('issue_updated'),
    });
  } catch (error) {
    console.error('Error reopening issue:', error);
  }
}

function deleteIssue() {
  $q
    .dialog({
      cancel: true,
      title: t('issue_delete_confirm_title'),
      message: t('issue_delete_confirm_question'),
    })
    .onOk(async () => {
      try {
        await sendEvent({
          event_type: 'ISSUE_DELETED',
          event_data: {
            issue_data: {
              _key: props.issueKey,
            },
          },
        });
        const work_order_key = store.state.traceability.working_job_data.wo_key;
        await store.dispatch('getIssues', { work_order_key });
        exit();
        notify({
          message: t('issue_delete_success'),
        });
      } catch (error) {
        console.error('Error deleting issue:', error);
      }
    });
}

function exit() {
  router.back();
}

// Lifecycle
onMounted(() => {
  store.dispatch('loadUsers');
  getHistory();
});
</script>

<template>
  <div class="absolute-full row q-pa-md">

    <!-- LEFT SECTION -->
    <div class="col-8 column">
      <IssueHeader :issue="issue" />
      <div class="q-ml-xl q-px-xl">
        <div v-for="m, index in messages" :key="m._key" class="q-mt-md q-ml-xl relative-position row full-width items-baseline justify-between">
          <div class="text-italic">{{ $formatDateTime(m.created, $i18n.locale, 'DATETIME_MED') }}</div>
          <div class="text-h4 highlight">MESSAGGIO PUBBLICATO</div>
          <BaseUserAvatar name_first :user="getUserData(m)"></BaseUserAvatar>
          <div style="position: absolute; left: -40px; top: 5; height: 100%; width: 32px">
            <div class="column full-height">
              <div style="height: 13px; width: 13px; border-radius: 100%; background-color: #888; border: 5px solid var(--surface-1); box-sizing: content-box; z-index:99"></div>
              <div v-if="index < messages.length -1" style="position: absolute; height: 100%; left: 11px; top: 20px; width: 1px; background-color: #fff3;"></div>
            </div>
          </div>
        </div>
      </div>

      <q-space />


      <div class="row q-pa-md q-gutter-lg">
        <template v-if="issue.open">
          <q-btn color="theme-green" label="Chiudi segnalazione" />
          <q-btn v-if="issue.critical" color="theme-orange" label="Segna come non critica" />
          <q-btn v-else color="theme-red" label="trasforma in critica" />
        </template>
        <template v-else>
          <q-btn color="theme-orange" label="riapri segnalazione" />
          <q-btn color="theme-red" label="riapri come critica" />
        </template>
        <q-space />
        <q-btn color="theme-grey" label="torna all'elenco" @click="goToJobIssueList"/>
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
          color="theme-green"
          :label="$t('send')"
          @click="postMessage">
        </q-btn>
      </div>
    </div>
  </div>
</template>

<script>
import IssueHeader from '@/components/IssueHeader.vue'
import enrichIssue from '@/mixins/issues.js'
import Message from '@/components/Message.vue'
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'

export default {

  name: 'IssueDetail',

  components: {
    IssueHeader,
    Message,
    BaseUserAvatar
  },

  mixins: [enrichIssue],

  props: {
    // from router
    issue_key: {
      type: String,
      required: true
    }
  },

  data() {
    return {
      messages: [],
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
    }
  },

  methods: {
    getMessages() {
      this.$api.get('message', { params: { issue_key: this.issue._key }})
      .then(resp => this.messages = resp.data)
    },

    getAvatarSrc(user) {
      return this.base_path + (user.name + user.surname).replace(/\s+/g, '') + '.jpg'
    },

    getUserData(message) {
      const user = this.$store.getters.user_data(message._from.split('/')[1])
      return {
        ...user,
        full_name: user.name + ' ' + user.surname,
        src: this.getAvatarSrc(user)
      }
    },

    goToJobIssueList() {
      this.$router.push({
        name: 'jobIssues',
        params: {
          job_key: this.$route.params.job_key
        }
      })
    },

    postMessage() {
      const data = {
        sender: `User/${this.$store.state.session.user._key}`,
        recipient: `Issue/${this.issue._key}`,
        content: this.new_message
      }
      this.loading = true
      this.$api.post('message', data).then(() => {
        this.new_message = ''
        this.getMessages()
        this.loading = false
      })
    }
  },

  created() {
    this.$store.dispatch('loadUsers')
    this.getMessages()
  }
}
</script>

<style lang="css" scoped>
</style>

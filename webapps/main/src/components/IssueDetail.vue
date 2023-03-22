<template>
  <div class="absolute-full row">
    <div class="col-8">
      <IssueHeader :issue="issue" />
      <div class="row">
      <q-timeline class="q-ml-xl col-6" color="theme-grey">
        <q-timeline-entry
          v-for="m, index in messages"
          :key="index"
          :title="getUserData(m).full_name"
          :avatar="getUserData(m).src">
          <div style="white-space: pre-line">
            {{ m.content }}
          </div>
        </q-timeline-entry>
      </q-timeline>
      <div class="col">
          <div v-for="n in 6" :key="n" class="q-mt-md q-ml-xl relative-position" style="z-index: 0">
            <div>Time</div>
            <div>Name</div>
            <div>Content</div>
            <div style="position: absolute; left: -40px; top: 0; height: 100%; width: 32px">
              <div class="column full-height">
                <div style="height: 32px; width: 32px; border-radius: 100%; background-color: #888; border: 4px solid green; box-sizing: content-box;"></div>
                <div style="position: absolute; height: 100%; left: 49%; width: 2px; background-color: red;"></div>
              </div>
            </div>
          </div>
      </div>
      </div>
    </div>
    <q-separator vertical inset spaced />
    <div class="col column q-pa-lg full-height">
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
<!--             <template v-else>
              <div class="row justify-center full-width">
                <q-spinner-bars v-for="n in 10" size="lg" style="margin-left: -6px"/>
              </div>
            </template> -->
          </div>
         <!--  <q-btn
            round
            dense
            color="theme-red"
            icon="mdi-microphone"
            class="q-ml-md"
            @click="record">
          </q-btn> -->
        </div>
        <q-btn
          class="full-width q-mt-md"
          padding="sm"
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

export default {

  name: 'IssueDetail',

  components: {
    IssueHeader,
    Message
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
        full_name: user.name + ' ' + user.surname,
        src: this.getAvatarSrc(user)
      }
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
    },

    async record(constraints) {
      const downloadLink = document.getElementById('download');
      const stopButton = document.getElementById('stop');


      const handleSuccess = function(stream) {
        const options = {mimeType: 'audio/webm'};
        const recordedChunks = [];
        const mediaRecorder = new MediaRecorder(stream, options);

        mediaRecorder.addEventListener('dataavailable', function(e) {
          if (e.data.size > 0) recordedChunks.push(e.data);
        });

        mediaRecorder.addEventListener('stop', function() {
          downloadLink.href = URL.createObjectURL(new Blob(recordedChunks));
          downloadLink.download = 'acetest.wav';
        });

        stopButton.addEventListener('click', function() {
          mediaRecorder.stop();
        });

        mediaRecorder.start();
      };

      navigator.mediaDevices.getUserMedia({ audio: true, video: false })
      .then(handleSuccess);
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

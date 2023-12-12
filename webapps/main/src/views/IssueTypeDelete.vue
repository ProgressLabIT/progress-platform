<template>
  <BaseDialog :show="true" @close="$router.back()">
    <q-card square class="surface1 q-pa-md" style="max-width: 600px">
      <q-card-section class="text-h3 display highlight">
        {{ $capitalize($t('issue_type_delete_title')) }}
      </q-card-section>

      <transition name="slide-fade" mode="out-in">
        <div v-if="stage == 'confirm'" key="confirm">
          <q-card-section>
            <div>
              {{ $capitalize($t('issue_type_delete_question')) }}
            </div>
            <div class="text-h3 uppercase highlight q-mt-md">
              {{ issueType.name }}
            </div>
          </q-card-section>

          <q-card-section>
            <div class="row justify-between">
              <q-btn
                color="theme-red"
                :label="$t('confirm')"
                @click="deleteIssueType"
              >
              </q-btn>
              <q-btn
                color="theme-grey"
                :label="$t('cancel')"
                class="q-ml-md"
                @click="$router.back()"
              >
              </q-btn>
            </div>
          </q-card-section>
        </div>

        <div v-else key="success">
          <q-card-section>
            <div class="row justify-between">
              <span class="q-mr-xl">
                {{ $capitalize($t('issue_type_delete_success')) }}
              </span>
              <q-btn
                color="theme-grey"
                :label="$t('close')"
                @click="$router.push({ name: 'issueTypeLibrary' })"
              >
              </q-btn>
            </div>
          </q-card-section>
        </div>
      </transition>
    </q-card>
  </BaseDialog>
</template>

<script>
import { api } from '@/boot/axios.js';
import BaseDialog from '@/components/BaseDialog.vue';

export default {
  name: 'IssueTypeDelete',

  components: {
    BaseDialog,
  },

  props: {
    issueType: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      showModal: true,
      stage: 'confirm',
    };
  },

  methods: {
    deleteIssueType() {
      api
        .delete(`issue-type/${this.issueType._key}`)
        .then(async () => {
          // reload users from backend to make sure archived user is not present
          this.stage = 'success';
          this.$store.dispatch('getIssueTypes');
        })
        .catch((err) => {
          // Operation is in use in some process
          if (err.response.status === 403) {
            const error_message = this.$t('issue_type_alerts_in_use') + ': ';
            window.alert(
              error_message + err.response.data.detail.product_codes,
            );
            this.$router.back();
          } else {
            window.alert(this.$t('issue_type_alerts_delete_general_error'));
          }
        });
    },
  },
};
</script>

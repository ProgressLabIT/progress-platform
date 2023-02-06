<template>
  <BaseDialog :show="true" @close="$router.back()">
    <q-card square class="surface1 q-pa-md" style="max-width: 600px">

      <q-card-section class="text-h3 display highlight">
        {{ $capitalize($t('operation.delete_title')) }}
      </q-card-section>

      <transition name="slide-fade" mode="out-in">

        <div v-if="stage == 'confirm'" key="confirm">
          <q-card-section>
            <div>
              {{ $capitalize($t('operation.delete_question')) }}?
            </div>
            <div class="text-h3 uppercase highlight q-mt-md">
              {{ operation.name }}
            </div>
          </q-card-section>

          <q-card-section>
          <div class="row justify-between">
            <q-btn
              color="theme-red"
              @click="deleteOperation"
              :label="$t('confirm')">
            </q-btn>
            <q-btn
              color="theme-grey"
              @click="$router.back()"
              :label="$t('cancel')"
              class="q-ml-md">
            </q-btn>
          </div>
          </q-card-section>
        </div>

        <div v-else key="success">
          <q-card-section>
            <div class="row justify-between">
              <span class="q-mr-xl">
                {{ $capitalize($t('operation.delete_success')) }}
              </span>
              <q-btn
                color="theme-grey"
                @click="$router.push({ name: 'operationLibrary' })"
                :label="$t('close')">
              </q-btn>
            </div>
          </q-card-section>
        </div>

      </transition>
    </q-card>

  </BaseDialog>
</template>

<script>
import BaseDialog from '@/components/BaseDialog.vue'
import { api } from '@/boot/axios.js'
import NonExistentOperationGuard from "@/mixins/NonExistentOperationGuard.js"

export default {

  name: 'OperationDelete',

  components: {
    BaseDialog
  },

  mixins: [NonExistentOperationGuard],

  props: {
    operation: {
      type: Object
    }
  },

  data () {
    return {
      showModal: true,
      stage: 'confirm',
    }
  },

  methods:{
    deleteOperation() {
      api.delete(`operation/${this.operation._key}`)
      .then( async () => {
        // reload users from backend to make sure archived user is not present
        await this.$store.dispatch('getOperations')
        this.stage="success"
      })
      .catch(err => {
        // Operation is in use in some process    
        if (err.response.status === 403) {
          const error_message = this.$tc('operation.alerts.op_in_use') + ": "
          window.alert(error_message + err.response.data.detail.product_codes)
          this.$router.back()
        }
        else {
          window.alert(this.$tc('operation.alerts.delete_general_error'))
        }
      })
    }
  },
}
</script>

<style lang="css" scoped>
</style>

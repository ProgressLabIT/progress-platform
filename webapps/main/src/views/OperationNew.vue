<template>
  <BaseModalForm
    :show="true"
    id="new-product-form"
    @submit="submit"
    max_width="700px"
    @cancel="$router.back()">

     <template #title>
      {{ $t('operation.new') }}
    </template>

    <template #form>
      <div class="row q-col-gutter-xl" style="min-width: 400px">
        <div class="col-6">
          <q-input
            :label="$capitalize($t('name'))"
            v-model="new_operation_data.name"
            clearable>
          </q-input>
        </div>

        <div class="col-6">
          <q-input
            :label="$capitalize($t('code'))"
            v-model="new_operation_data.code"
            clearable>
          </q-input>
        </div>

        <div class="col-12">
          <q-input
            type="textarea"
            clearable
            :label="$capitalize($t('description'))"
            v-model="new_operation_data.description">
          </q-input>
        </div>
      </div>
    </template>


  </BaseModalForm>
</template>

<script>
import BaseModalForm from '@/components/BaseModalForm.vue'

export default {

  name: 'OperationNew',

  components: { BaseModalForm },

  data () {
    return {
      stage: 'form',
      valid: true,
      fields: [
        { required: true, model: 'name', component: 'v-text-field' },
        { required: false, model: 'code', component: 'v-text-field' },
        { required: true, model: 'description', component: 'v-textarea' },
      ],
      new_operation_data: {
        name: undefined,
        code: undefined,
        description: undefined
      }
    }
  },

  methods: {
    submit() {
      if (!this.new_operation_data.name) {
        window.alert(c(this.$tc('operations.alerts.op_name_missing')))
      }

      else {
        this.$store.dispatch('createOperation', this.new_operation_data)
        .then( (new_operation_key) => {
          this.$router.push({
            name: 'operationDetail',
            params: {
              operation_key: new_operation_key
            }
          })
        })
        .catch( err => {
          if (err.response.status === 409) {
            window.alert(c(this.$tc('operations.alerts.op_name_used')))
          }
          else { window.alert(err) }
        })
      }
    }
  }
}
</script>

<style lang="css" scoped>
</style>

<template>
  <div class="q-mb-md">
    <div class="row items-start j">
      <q-card square bordered flat class="surface2 q-pa-sm col q-mr-md">
        <div class="weight-bold text-italic q-mb-sm">
          {{ user.name }} {{ user.surname }}
        </div>
        <div style="white-space: pre-line">
          {{ message.content }}
        </div>
      </q-card>
      <BaseUserAvatar :user="user" name_class="text-low" :show_name="false"/>
    </div>
    <div class="text-italic text-low smaller q-mt-sm">
      {{ datetime }}
    </div>
  </div>
</template>

<script>
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'

export default {

  name: 'Message',

  components: {
    BaseUserAvatar
  },

  props: {
    message: {
      type: Object,
      required: true
    }
  },

  computed: {
    user() {
      return this.$store.getters.user_data(this.message._from.split('/')[1])
    },

    datetime() {
      const config = {
        year: '2-digit',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit',
        weekday: 'short'
      }
      return this.$capitalize(this.$formatDateTime(this.message.created, this.$i18n.locale, config))
    }
  }
}
</script>

<style lang="css" scoped>
</style>

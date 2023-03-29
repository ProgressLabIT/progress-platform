<template>
  <q-item class="q-py-md" :clickable="clickable">
    <q-item-section
      avatar
      @mouseenter="over_icon=true"
      @mouseleave="over_icon=false">
      <q-btn flat :icon="icon" size="lg" @click.stop="show_type_picker=true">
        <q-tooltip class="text-uppercase">
          {{ $t('issue_edit_type') }}
        </q-tooltip>
      </q-btn>
    </q-item-section>
    <q-item-section>
      <q-item-label class="weight-bold text-h4 row">
        <div class="q-mr-md">{{ issue.type_name || $t('issue') }}</div>
        <div>#{{ issue._key }}</div>
      </q-item-label>
    </q-item-section>
    <q-item-section top class="display col-auto weight-bold text-uppercase">
      <q-chip :color="issue.badge.color">
        {{ issue.badge.text }}
      </q-chip>
    </q-item-section>

    <!-- ISSUE TYPE PICKER -->
    <BaseDialog :show="show_type_picker">
      <q-card class="q-pa-md surface1" style="min-width: 400px;">
        <q-card-section class="text-h3 highlight">
          {{ $t('issue_update_type') }}
        </q-card-section>
        <q-card-section>
          <BaseAutocompleteIssueType
            :value="new_issue_type"
            @select="(value) => new_issue_type=value">
          </BaseAutocompleteIssueType>
        </q-card-section>
        <q-card-section class="row justify-between">
          <q-btn
            color="theme-grey"
            :label="$t('cancel')"
            @click="() => { show_type_picker=false; new_issue_type = {}}">
          </q-btn>
          <q-btn
            color="theme-blue"
            :label="$t('save')"
            @click="changeIssueType">
          </q-btn>
        </q-card-section>
      </q-card>
    </BaseDialog>
  </q-item>
</template>

<script>
import BaseDialog from '@/components/BaseDialog.vue'
import BaseAutocompleteIssueType from '@/components/BaseAutocompleteIssueType.vue'
import event from '@/mixins/event.js'

export default {

  name: 'IssueHeader',

  components: {
    BaseAutocompleteIssueType,
    BaseDialog
  },

  props: {
    issue: {
      type: Object,
      required: true
    },
    clickable: {
      type: Boolean,
      default: false
    }
  },

  mixins: [event],

  data() {
    return {
      over_icon: false,
      show_type_picker: false,
      new_issue_type: {}
    }
  },

  computed: {
    icon() {
      return this.over_icon ? 'mdi-pencil' : this.issue.icon || 'mdi-help'
    }
  },

  methods: {
    changeIssueType() {
      this.sendEvent({
        event_type: 'ISSUE_UPDATED',
        event_data: {
          issue_data: {
            _key: this.issue._key,
            issue_type: this.new_issue_type ? this.new_issue_type._key : null
          }
        }
      }).then(() => {
        this.$emit('type-change', this.new_issue_type ? this.new_issue_type._key : null)
        this.show_type_picker = false
      })
    }
  }
}
</script>

<style lang="css" scoped>
</style>

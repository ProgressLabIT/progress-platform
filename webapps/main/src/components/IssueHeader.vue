<template>
  <q-item class="q-py-md" :clickable="clickable">
    <q-item-section avatar>
      <q-icon flat :name="issue.icon || 'mdi-help'" size="lg" />
    </q-item-section>
    <q-item-section>
      <q-item-label class="weight-bold text-h4 row items-center">
        <div class="q-mr-md">{{ issue.issue_type_name || $t('issue') }}</div>
        <div>#{{ issue._key }}</div>
        <div class="col q-ml-xl">
          <q-btn flat round @click.stop="show_issue_update=true" icon="mdi-pencil" />
        </div>
      </q-item-label>
    </q-item-section>
    <q-item-section class="display col-auto weight-bold text-uppercase">
      <q-chip :color="issue.badge.color">
        {{ issue.badge.text }}
      </q-chip>
    </q-item-section>

    <!-- ISSUE EDIT DIALOG -->
    <IssueForm
      :show="show_issue_update"
      :issue="issue"
      mode="edit"
      @close="show_issue_update=false">
    </IssueForm>

  </q-item>
</template>

<script>
import BaseDialog from '@/components/BaseDialog.vue'
import IssueForm from '@/components/IssueForm.vue'
import BaseAutocompleteIssueType from '@/components/BaseAutocompleteIssueType.vue'
import event from '@/mixins/event.js'

export default {

  name: 'IssueHeader',

  components: {
    BaseAutocompleteIssueType,
    BaseDialog,
    IssueForm
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
      show_issue_update: false,
      new_issue_type: null
    }
  },

  computed: {
    icon() {
      return this.over_icon ? 'mdi-pencil' : this.issue.icon || 'mdi-help'
    },

    save_btn_color() {
      return this.new_issue_type == null
        ? 'theme-blue'
        : this.new_issue_type.critical
        ? 'theme-red'
        : 'theme-blue'
    },

    save_btn_label() {
      const base = this.$t('save')
      const critical = this.new_issue_type == null
        ? ''
        : this.new_issue_type.critical
        ? ' ' + this.$t('critical')
        : ''
      return base + critical
    }
  },

  methods: {
    changeIssueType() {
      const set_as_critical = this.new_issue_type ? this.new_issue_type.critical : false
      const event = {
        event_type: 'ISSUE_UPDATED',
        event_data: {
          issue_data: {
            _key: this.issue._key,
            issue_type: this.new_issue_type ? this.new_issue_type._key : null,
          }
        }
      }

      if (set_as_critical) {
        event.event_data.issue_data.critical = true
      }

      this.sendEvent(event).then(() => {
        this.$emit('type-change', this.new_issue_type ? this.new_issue_type._key : null)
        this.show_type_picker = false
      })
    }
  },
  watch: {
    show_type_picker() {
      if (this.show_type_picker == false) {
        this.new_issue_type = null
      }
    }
  }
}
</script>

<style lang="css" scoped>
</style>

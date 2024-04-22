<template>
  <q-item class="q-py-md" :clickable="clickable">
    <q-item-section avatar>
      <q-icon flat :name="issue.icon || 'mdi-help'" size="lg" />
    </q-item-section>
    <q-item-section>
      <q-item-label class="row items-center">
        <span class="weight-bold text-h4 q-mr-sm">
          {{ issue.issue_type_name || $t('serial') }}
        </span>
        <span class="smaller text-body2 text-uppercase low-text q-ml-md">
          <span class="q-mr-sm">
            {{ issue.phase_alias }}
          </span>
          <span>#{{ issue._key }}</span>
        </span>
        <div class="col q-ml-xl">
          <q-btn
            flat
            round
            icon="mdi-pencil"
            @click.stop="show_issue_update = true"
          >
            <q-tooltip>{{ $capitalize($t('edit')) }}</q-tooltip>
          </q-btn>

          <q-btn
            v-if="isAvailable"
            flat
            round
            icon="mdi-printer"
            class="q-ml-sm"
            @click.stop="openPrintDialog"
          >
            <q-tooltip>{{ $capitalize($t('print')) }}</q-tooltip>
          </q-btn>
        </div>
      </q-item-label>
    </q-item-section>
    <q-item-section class="display col-auto weight-bold text-uppercase">
      <q-chip :color="issue.badge.color">
        {{ issue.badge.text }}
      </q-chip>
    </q-item-section>

    <!-- SERIAL EDIT DIALOG -->
    <SerialForm
      :show="show_issue_update"
      :issue="issue"
      mode="edit"
      @close="show_issue_update = false"
    >
    </SerialForm>
  </q-item>
</template>

<script>
import SerialForm from '@/components/SerialForm.vue';
import { usePrintDialog } from '@/lib/print';
import event from '@/mixins/event.js';

export default {
  name: 'SerialHeader',

  components: {
    SerialForm,
  },

  mixins: [event],

  props: {
    issue: {
      type: Object,
      required: true,
    },
    clickable: {
      type: Boolean,
      default: false,
    },
  },

  emits: ['typeChange'],

  setup(props) {
    const { open: openPrintDialog, isAvailable } = usePrintDialog({
      context: 'issue_type',
      contextData: props.issue,
    });

    return {
      openPrintDialog,
      isAvailable,
    };
  },

  data() {
    return {
      over_icon: false,
      show_issue_update: false,
      new_issue_type: null,
    };
  },

  computed: {
    icon() {
      return this.over_icon ? 'mdi-pencil' : this.issue.icon || 'mdi-help';
    },

    save_btn_color() {
      return this.new_issue_type == null
        ? 'theme-blue'
        : this.new_issue_type.critical
          ? 'theme-red'
          : 'theme-blue';
    },

    save_btn_label() {
      const base = this.$t('save');
      const critical =
        this.new_issue_type == null
          ? ''
          : this.new_issue_type.critical
            ? ' ' + this.$t('critical')
            : '';
      return base + critical;
    },
  },
  watch: {
    show_type_picker() {
      if (this.show_type_picker == false) {
        this.new_issue_type = null;
      }
    },
  },

  methods: {
    changeIssueType() {
      const set_as_critical = this.new_issue_type
        ? this.new_issue_type.critical
        : false;
      const event = {
        event_type: 'ISSUE_UPDATED',
        event_data: {
          issue_data: {
            _key: this.issue._key,
            issue_type: this.new_issue_type ? this.new_issue_type._key : null,
          },
        },
      };

      if (set_as_critical) {
        event.event_data.issue_data.critical = true;
      }

      this.sendEvent(event).then(() => {
        this.$emit(
          'typeChange',
          this.new_issue_type ? this.new_issue_type._key : null,
        );
        this.show_type_picker = false;
      });
    },
  },
};
</script>

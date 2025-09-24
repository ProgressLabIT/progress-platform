<template>
  <q-item class="q-py-md" :clickable="clickable">
    <q-item-section avatar>
      <q-icon flat :name="issue.icon || 'mdi-help'" size="lg" />
    </q-item-section>
    <q-item-section>
      <q-item-label class="row items-center">
        <span class="weight-bold text-h4 q-mr-sm">
          {{ issue.issue_type_name || $t('issue') }}
        </span>
        <span class="smaller text-body2 text-uppercase low-text q-ml-md">
          <span>
            {{ issue.phase_alias }}
          </span>
          <span class="q-mx-sm">
            #{{ issue._key }}
          </span>
          <span>
            {{ $formatDateTime(issue.created) }}
          </span>
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

    <!-- ISSUE EDIT DIALOG -->
    <IssueForm
      :show="show_issue_update"
      :issue="issue"
      mode="edit"
      @cancel="show_issue_update = false"
    >
    </IssueForm>
  </q-item>
</template>

<script setup>
import { ref } from 'vue';
import IssueForm from '@/components/IssueForm.vue';
import { usePrintDialog } from '@/lib/print';

const props = defineProps({
  issue: {
    type: Object,
    required: true,
  },
  clickable: {
    type: Boolean,
    default: false,
  },
});


// Composables
const { open: openPrintDialog, isAvailable } = usePrintDialog({
  context: 'issue_type',
  contextData: props.issue,
});

// Reactive data
const show_issue_update = ref(false);
</script>

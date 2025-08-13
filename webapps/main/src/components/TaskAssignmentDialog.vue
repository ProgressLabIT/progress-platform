<template>
  <BaseModalForm
    :show="show"
    :loading="loading"
    :handle-close="handleCancel"
    @submit="handleSave"
    @cancel="handleCancel"
  >
    <template #title>
      {{ $t('edit_assignments') }}
    </template>

    <template #form>
      <div class="column q-gutter-md">
        <div class="text-h6">{{ $t('current_assignments') || 'Current assignments' }}</div>

        <q-list v-if="localAssignments.length">
          <q-item
            v-for="assignment in localAssignments"
            :key="assignment.user_key"
            class="q-pa-none"
          >
            <q-item-section>
              <BaseUserAvatar
                :user="store.getters.getUserByKey(assignment.user_key)"
                :size="'26px'"
              />
            </q-item-section>

            <q-item-section side>
              <q-btn
                v-if="assignment.role === 'owner'"
                flat
                round
                color="theme-blue"
                padding="0px"
                size="18px"
                icon="mdi-crown-circle"
              >
              </q-btn>
              <q-btn
                v-else
                flat
                round
                dense
                icon="mdi-circle-outline"
                padding="4px"
                size="14px"
                @click="makeOwner(assignment.user_key)"
              />
            </q-item-section>

            <q-item-section side>
              <q-btn
                flat
                round
                dense
                icon="mdi-close"
                size="sm"
                class="text-grey-6 hover-text-negative"
                @click="removeAssignment(assignment.user_key)"
              />
            </q-item-section>
          </q-item>
        </q-list>

        <div v-else class="text-italic text-grey-6">
          {{ $t('no_assignees') || 'No assignees' }}
        </div>

        <div class="text-h6 q-mt-md">{{ $t('add_user') || 'Add user' }}</div>
        <BaseAutocompleteUser
          :label="$t('select_user') || 'Select user'"
          :key-only="true"
          :clearable="true"
          @select="addAssignment"
        />
      </div>
    </template>
  </BaseModalForm>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import BaseAutocompleteUser from 'src/components/BaseAutocompleteUser.vue';
import BaseModalForm from 'src/components/BaseModalForm.vue';
import BaseUserAvatar from 'src/components/BaseUserAvatar.vue';

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  assignments: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['save', 'cancel', 'update:assignments']);

const store = useStore();
const { t: $t } = useI18n();

const localAssignments = ref([]);

// Watch for dialog visibility to reset state
watch(
  () => props.show,
  (isShown) => {
    if (isShown) {
      localAssignments.value = [...(props.assignments || [])];
    }
  }
);

function addAssignment(user_key) {
  if (user_key && !localAssignments.value.some(a => a.user_key === user_key)) {
    // Default role is participant, unless this is the first user (then owner)
    const role = localAssignments.value.length === 0 ? 'owner' : 'participant';
    localAssignments.value.push({
      user_key,
      role,
    });
  }
}

function removeAssignment(userKey) {
  const index = localAssignments.value.findIndex(a => a.user_key === userKey);
  if (index > -1) {
    localAssignments.value.splice(index, 1);
  }
}

function makeOwner(userKey) {
  const assignment = localAssignments.value.find(a => a.user_key === userKey);
  if (assignment) {
    // If changing to owner, make sure only one owner exists
    localAssignments.value.forEach(a => {
      if (a.user_key !== userKey && a.role === 'owner') {
        a.role = 'participant';
      }
    });
    assignment.role = 'owner';
  }
}

function handleSave() {
  emit('save', [...localAssignments.value]);
}

function handleCancel() {
  // Reset to original assignments
  localAssignments.value = [...(props.assignments || [])];
  emit('cancel');
}
</script>

<style lang="sass" scoped>
// No specific styles needed for this component
</style>

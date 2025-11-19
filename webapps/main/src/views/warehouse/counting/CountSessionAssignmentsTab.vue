<template>
    <div class="row full-height">

      <!-- LEFT COLUMN: ASSIGNMENT LIST -->
      <div class="col-3 column">
        <!-- ASSIGNMENT LIST -->
        <div class="row items-center justify-between q-my-xs q-px-md">
          <div class="text-h5 uppercase">
            {{ $t('warehouse.counting.assignments') }}
          </div>
          <div class="col-auto row items-center q-gutter-x-sm">
            <div class="smaller text-low">
              {{ coveragePercentage.toFixed(1) }}%
            </div>
            <q-circular-progress
              size="18px"
              :value="coveragePercentage"
              track-color="theme-grey"
              color="white"
            />
          </div>
        </div>

        <q-separator inset class="q-my-sm" />

        <!-- ADD ASSIGNMENT BUTTON -->
        <BaseAutocompleteUser
            dense
            :label="$capitalize($t('warehouse.counting.add_assignment'))"
            :clearable="false"
            :key-only="true"
            @select="addAssignment"
            class="q-mx-md q-my-sm"
          />

        <q-scroll-area class="col" style="max-height: 100%">
          <q-list>
            <q-item
              v-for="item in assignments"
              :key="item.user_key"
              class="assignment-item"
              :class="selectedAssignment?.user_key === item.user_key ? 'selected-assignment text-high' : ''"
              clickable
              @click="selectedAssignment = item"
            >
              <q-item-section>
                <BaseUserAvatar
                  :user="getUser(item.user_key)"
                  :show-name="true"
                  dense
                />
              </q-item-section>
              <q-item-section side>
                {{ getAssignmentCount(item) }}
              </q-item-section>
              <q-item-section side>
                <q-btn
                  flat
                  round
                  icon="mdi-delete"
                  size="sm"
                  @click.stop="removeAssignment(item.user_key)"
                />
              </q-item-section>
            </q-item>
          </q-list>
        </q-scroll-area>
      </div>

      <q-separator vertical />

      <!-- CENTER COLUMN: AVAILABLE ITEMS -->
      <div class="col column full-height">
        <div class="row items-center justify-between q-col-gutter-x-lg q-px-md">
          <div class="col-auto row items-center q-gutter-x-sm">
            <span class="q-mr-sm text-h5 uppercase">
              {{ $t('shown', 2) }}
            </span>
            <q-chip color="theme-grey" size="sm">
              <strong>
                {{ currentShownCount }}
              </strong>
              <span class="q-mx-xs">
                {{ $t('of') }}
              </span>
              <strong>
                {{ currentTotalCount }}
              </strong>
            </q-chip>
            <q-icon
              name="mdi-account-group"
              size="20px"
              class="q-ml-sm"
            />
            <q-chip
              color="theme-grey"
              size="sm"
              clickable
              @click="showMultiAssignedOnlyCenter = !showMultiAssignedOnlyCenter"
              :outline="!showMultiAssignedOnlyCenter"
            >
              <strong>{{ centerColumnMultiAssignedCount }}</strong>
            </q-chip>
          </div>
          <q-btn
            size="xs"
            padding="xs sm"
            icon="mdi-checkbox-marked-outline"
            :label="$t('select_all')"
            color="theme-grey"
            class="q-ml-md"
            @click="selectAllItems"
          />
        </div>

        <q-separator inset class="q-my-sm" />

        <div class="col-auto row q-my-sm items-center q-px-md justify-between q-gutter-x-lg">
          <q-input
            v-model="searchText"
            filled
            dense
            debounce="200"
            :placeholder="$capitalize($t('search'))"
            class="col"
          >
            <template #append>
              <q-icon name="mdi-magnify" />
            </template>
          </q-input>
        </div>

        <CountSessionAssignmentsProductList
          v-if="sessionType === 'product'"
          ref="productListRef"
          v-model:selected-assignment="selectedAssignment"
          :items="items"
          :assignments="assignments"
          :disable-assigned-items="disableAssignedItems"
          :search-text="searchText"
          :show-multi-assigned-only="showMultiAssignedOnlyCenter"
          @update:stats="updateStats"
        />

        <CountSessionAssignmentsPositionTree
          v-else
          ref="positionTreeRef"
          v-model:selected-assignment="selectedAssignment"
          :nodes="positionTreeNodes"
          :assignments="assignments"
          :disable-assigned-items="disableAssignedItems"
          :search-text="searchText"
          :show-multi-assigned-only="showMultiAssignedOnlyCenter"
          @update:stats="updateStats"
        />
      </div>

      <q-separator vertical />

      <!-- RIGHT COLUMN: SELECTED ITEMS -->
      <div class="col column full-height">
        <div class="col-auto row items-center q-px-md justify-between">
          <div class="row items-center q-gutter-x-sm">
            <span class="text-h5 uppercase">
              {{ $t('warehouse.counting.selected') }}
            </span>
            <q-chip color="theme-grey" size="sm">
              <strong>
                {{ filteredAssignedItems?.length }}
              </strong>
              <span class="q-mx-xs">
                {{ $t('of') }}
              </span>
              <strong>
                {{ selectedItemsForAssignment?.length }}
              </strong>
            </q-chip>
            <template v-if="props.sessionType === 'product'">
              <q-icon
                name="mdi-account-group"
                size="20px"
                class="q-ml-sm"
              />
              <q-chip
                color="theme-grey"
                size="sm"
                clickable
                @click="showMultiAssignedOnlyRight = !showMultiAssignedOnlyRight"
                :outline="!showMultiAssignedOnlyRight"
              >
                <strong>{{ rightColumnMultiAssignedCount }}</strong>
              </q-chip>
            </template>
          </div>
          <q-btn
            size="xs"
            padding="xs sm"
            icon="mdi-checkbox-blank-off-outline"
            :label="$t('deselect_all')"
            color="theme-grey"
            class="q-ml-md"
            @click="clearSelectedItems"
          >
          </q-btn>
        </div>

        <q-separator inset class="q-my-sm" />

        <div class="q-px-md col-auto q-my-sm">
          <q-input
            v-model="selectedItemsSearchText"
            filled
            dense
            debounce="200"
            :placeholder="$capitalize($t('search'))"
          >
            <template #append>
              <q-icon name="mdi-magnify" />
            </template>
          </q-input>
        </div>
        <q-virtual-scroll
          v-slot="{ item }"
          class="col fit"
          style="max-height: 100%"
          :items="filteredAssignedItems"
        >
          <q-item :key="item._key || item.key" style="min-height: none">
            <q-item-section side>
              <q-btn
                flat
                round
                icon="mdi-close"
                size="sm"
                @click="removeSelectedItem(item)"
              />
            </q-item-section>
            <q-item-section>
              <q-item-label class="highlight">
                {{ item.code || item.label }}
              </q-item-label>
              <q-item-label
                v-if="item.description"
                caption
                class="ellipsis"
              >
                {{ item.description }}
              </q-item-label>
            </q-item-section>
            <q-item-section v-if="getItemAssignees(item).length > 1" side>
              <div class="row items-center q-gutter-x-xs">
                <q-icon
                  name="mdi-account-group"
                  size="20px"
                >
                  <q-tooltip>
                    <div v-for="user in getItemAssignees(item)" :key="user._key">
                      {{ user.name }} {{ user.surname }}
                    </div>
                  </q-tooltip>
                </q-icon>
                <span class="text-caption">{{ getItemAssignees(item).length }}</span>
              </div>
            </q-item-section>
          </q-item>
        </q-virtual-scroll>
      </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { Notify } from 'quasar';
import { useWildcardToRegex } from '@/composables/useWildcardToRegex';
import { useCountSessionStore } from '@/stores/countSession';
import BaseAutocompleteUser from '@/components/BaseAutocompleteUser.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import CountSessionAssignmentsProductList from './CountSessionAssignmentsProductList.vue';
import CountSessionAssignmentsPositionTree from './CountSessionAssignmentsPositionTree.vue';

const props = defineProps({
  sessionType: {
    type: String,
    required: true,
  },
  disableAssignedItems: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:disableAssignedItems']);

const { t: $t } = useI18n();
const store = useStore();
const countSessionStore = useCountSessionStore();
const { wildcardToRegex } = useWildcardToRegex();

const searchText = ref('');
const selectedAssignment = ref(null);
const selectedItemsSearchText = ref('');
const showMultiAssignedOnlyCenter = ref(false);
const showMultiAssignedOnlyRight = ref(false);
const productListRef = ref(null);
const positionTreeRef = ref(null);

// Stats for center column (updated by child components)
const currentShownCount = ref(0);
const currentTotalCount = ref(0);
const currentMultiAssignedCount = ref(0);

const assignments = defineModel('assignments', { default: () => [] }); // [{ user_key, items: [] }]

// Watch assignments to auto-select first assignment when loaded
watch(
  assignments,
  (newAssignments) => {
    if (newAssignments.length > 0 && !selectedAssignment.value) {
      selectedAssignment.value = newAssignments[0];
    } else if (newAssignments.length === 0) {
      selectedAssignment.value = null;
    }
  },
  { immediate: true },
);

// Reset stats when session type changes (optional, helps avoid flicker of old stats)
watch(() => props.sessionType, () => {
  currentShownCount.value = 0;
  currentTotalCount.value = 0;
  currentMultiAssignedCount.value = 0;
  searchText.value = '';
});

function updateStats(stats) {
  currentShownCount.value = stats.shownCount;
  currentTotalCount.value = stats.totalCount;
  currentMultiAssignedCount.value = stats.multiAssignedCount;
}

// Computed properties

const filteredAssignedItems = computed(() => {
  let result = selectedItemsForAssignment.value;

  // Apply search filter
  if (selectedItemsSearchText.value) {
    const regex = wildcardToRegex(selectedItemsSearchText.value);
    result = result.filter((a) => regex.test(a.code || a.label));
  }

  // Apply multi-assignment filter for right column
  if (showMultiAssignedOnlyRight.value) {
    result = result.filter((item) => {
      const assignees = getItemAssignees(item);
      return assignees.length > 1;
    });
  }

  return result;
});

const assignedItemKeys = computed(() => {
  const keys = new Set();
  assignments.value?.forEach((assignment) => {
    assignment?.items?.forEach((item) => {
      keys.add(item._key || item.key);
    });
  });
  return keys;
});

const selectedItemsForAssignment = computed(() => {
  if (!selectedAssignment.value) return [];
  return selectedAssignment.value.items || [];
});

const coveragePercentage = computed(() => {
  if (props.sessionType === 'position') {
    // Position mode: use smart coverage calculation with position lookup
    const positionLookup = countSessionStore.positionLookup;
    return countSessionStore.sessionCoverage(assignedItemKeys.value, positionLookup);
  } else {
    // Product mode: simple ratio calculation
    const total = currentTotalCount.value || countSessionStore.items.length;
    if (total === 0) return 0;
    return (assignedItemKeys.value.size / total) * 100;
  }
});

const centerColumnMultiAssignedCount = computed(() => {
  return currentMultiAssignedCount.value;
});

const rightColumnMultiAssignedCount = computed(() => {
  return selectedItemsForAssignment.value.filter((item) => {
    const assignees = getItemAssignees(item);
    return assignees.length > 1;
  }).length;
});

const positionTreeNodes = computed(() => countSessionStore.positionTree);

// Computed properties for items from store
const items = computed(() => countSessionStore.items);

// Methods

async function loadItems() {
  try {
    // Set the session type in the store
    countSessionStore.setSessionType(props.sessionType);
    // Load items from the store
    await countSessionStore.loadItems();
  } catch (error) {
    Notify.create({
      type: 'negative',
      message: $t('warehouse.counting.items_load_error'),
      color: 'theme-red',
    });
  }
}
function getUser(user_key) {
  return store.getters.operator_list().find((u) => u._key === user_key);
}

function getAssignmentCount(assignment) {
  return assignment.items?.length || 0;
}

function addAssignment(user_key) {
  if (!user_key || assignments.value.some((a) => a.user_key === user_key)) {
    return;
  }
  assignments.value.push({
    user_key,
    items: [],
  });
  selectedAssignment.value = assignments.value[assignments.value.length - 1];
}

function removeAssignment(user_key) {
  const index = assignments.value.findIndex((a) => a.user_key === user_key);
  if (index > -1) {
    assignments.value.splice(index, 1);
    if (assignments.value.length === 0) {
      selectedAssignment.value = null;
    } else if (selectedAssignment.value?.user_key === user_key) {
      // If we deleted the selected assignment, select another one
      selectedAssignment.value = assignments.value[0];
    }
  }
}

function getItemAssignees(item) {
  const itemKey = item._key || item.key;
  const assignees = [];
  assignments.value?.forEach((assignment) => {
    if (assignment.items?.some((i) => (i._key || i.key) === itemKey)) {
      const user = getUser(assignment.user_key);
      if (user) assignees.push(user);
    }
  });
  return assignees;
}

function removeSelectedItem(item) {
  if (!selectedAssignment.value) return;
  const assignment = selectedAssignment.value;
  if (!assignment.items) return;

  const index = assignment.items.findIndex(
    (i) => (i._key || i.key) === (item._key || item.key),
  );
  if (index > -1) {
    assignment.items.splice(index, 1);
  }
}

function clearSelectedItems() {
  if (!selectedAssignment.value) return;

  const assignment = selectedAssignment.value;
  if (!assignment.items) return;

  // Get keys of items that are currently filtered/visible
  const visibleKeys = new Set(
    filteredAssignedItems.value.map((item) => item._key || item.key)
  );

  // Remove only visible items
  assignment.items = assignment.items.filter(
    (item) => !visibleKeys.has(item._key || item.key)
  );
}

function selectAllItems() {
  if (props.sessionType === 'product') {
    productListRef.value?.selectAll();
  } else {
    positionTreeRef.value?.selectAll();
  }
}

// Load items on mount
onMounted(async () => {
  await loadItems();
});

// Watch session type to reload items
watch(
  () => props.sessionType,
  async (newType, oldType) => {
    // Only react if type actually changed
    if (newType === oldType) return;

    // Load new items for the selected type (store will handle reset)
    await loadItems();
  }
);

</script>

<style scoped lang="sass">

.selected-assignment::before
  content: ''
  position: absolute
  left: 0
  top: 0
  bottom: 0
  width: 2px
  background-color: var(--q-primary)

.selected-assignment :deep(.q-item__section)
  font-weight: 600
</style>

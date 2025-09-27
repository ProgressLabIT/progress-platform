<template>
    <!-- <div
      v-if="showThread"
      class="thread full-height"
    ></div> -->
    <div class="timeline-row">
      <q-item
        clickable
        class="q-mt-md justify-between full-width items-baseline timeline-item"
        @click="toggleExpanded()"
      >
      <!-- TIMELINE DOT & THREAD -->
      <q-item-section side>
        <q-avatar size="13px" color="theme-grey"></q-avatar>
      </q-item-section>

      <!-- TIMESTAMP -->
      <q-item-section
        class="text-italic q-pr-sm"
        style="max-width: 200px"
      >
        {{ formattedTimestamp }}
      </q-item-section>

      <!-- EVENT TYPE -->
      <q-item-section class="text-h4 highlight text-uppercase">
        <q-item-label>
          {{ $t(`events.${event.event_type}`) }}
        </q-item-label>
        <q-item-label caption @click="goToContext()" class="hover-underline">
          <span class="text-uppercase">{{ event.context_name }}</span> {{ event.context_code }}
          <q-icon :name="event.context_icon" />
        </q-item-label>
      </q-item-section>

      <!-- EVENT USER -->
      <q-item-section class="col-auto row items-center">
        <BaseUserAvatar name_first :user="userData" />
      </q-item-section>
      <q-item-section side>
        <q-icon
          :name="isExpanded ? 'mdi-chevron-up' : 'mdi-chevron-down'"
          class="q-ml-sm text-grey-6"
          size="sm"
        />
      </q-item-section>
      </q-item>


      <!-- EXPANDABLE DETAILS -->
      <q-slide-transition>
        <div v-show="isExpanded" ref="expandedContent" class="q-ml-md q-mb-md q-px-xl full-width">
          <q-card flat bordered square class="q-pa-md">
            <div class="column q-gutter-sm">
              <div
                v-for="detail in eventDetails"
                :key="detail.label"
                class="row q-gutter-md"
              >
                <div class="col-3 text-weight-medium">
                  {{ detail.label }}:
                </div>
                <div class="col">
                  <pre v-if="detail.type === 'json'" class="smaller q-ma-none">{{ detail.value }}</pre>
                  <span v-else>{{ detail.value }}</span>
                </div>
              </div>
            </div>
          </q-card>
        </div>
      </q-slide-transition>
    </div>

</template>

<script setup>
import { computed, ref, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { capitalize } from '@/boot/filters';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import { formatDateTime } from '@/lib/TimeHandling';

const props = defineProps({
  event: {
    type: Object,
    required: true,
  },
  showThread: {
    type: Boolean,
    default: false,
  },
  userData: {
    type: Object,
    required: true,
  },
});

const { t: $t, locale } = useI18n();
const router = useRouter();

// Reactive state for expansion
const isExpanded = ref(false);
const expandedContent = ref(null);
const expandedHeight = ref(0);

// Toggle expansion method
const toggleExpanded = async () => {
  console.log('toggleExpanded', isExpanded.value);
  isExpanded.value = !isExpanded.value;

  if (isExpanded.value) {
    // Wait for DOM update, then measure expanded content
    await nextTick();
    if (expandedContent.value) {
      expandedHeight.value = expandedContent.value.offsetHeight;
    }
  } else {
    expandedHeight.value = 0;
  }
};

const formattedTimestamp = computed(() => {
  const config = {
    year: '2-digit',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
    weekday: 'short',
  };
  return capitalize(formatDateTime(props.event.timestamp, locale.value, config));
});

// Format event details for display
const eventDetails = computed(() => {
  const excludedFields = [
    '_id', '_rev', 'event_type', 'timestamp', 'user_key', 'user_session_key',
    'context_type', 'context_key', 'context_name', 'context_code', 'context_icon',
    'primary', 'event_group'
  ];

  const details = [];

  Object.entries(props.event).forEach(([key, value]) => {
    if (!excludedFields.includes(key) && value !== null && value !== undefined && value !== '') {
      let displayValue = value;
      let type = 'text';

      // Handle different value types
      if (typeof value === 'object') {
        displayValue = JSON.stringify(value, null, 2);
        type = 'json';
      } else if (Array.isArray(value)) {
        displayValue = JSON.stringify(value, null, 2);
        type = 'json';
      }

      details.push({
        label: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value: displayValue,
        type: type
      });
    }
  });

  return details;
});

const goToContext = () => {
  router.push({ name: 'taskScreen', params: { taskKey: props.event.context_key } });
};



</script>

<style lang="sass" scoped>
.dot
  height: 13px
  width: 13px
  border-radius: 100%
  background-color: #888
  border: 5px solid var(--surface-2)
  box-sizing: content-box
  z-index:99

.thread
  position: absolute
  height: 100%
  left: 11px
  top: 20px
  width: 1px
  background-color: #fff3
  transition: height 0.3s ease

.timeline-row
  position: relative
  &::before
    content: ''
    position: absolute
    left: 22px
    top: 40px
    bottom: -20px
    width: 1px
    border-left: 1px solid #fff3
    background-color: #fff3

  &:last-child::before
    display: none
</style>

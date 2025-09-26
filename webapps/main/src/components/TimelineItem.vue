<template>
  <q-item
    class="q-mt-md relative-position row justify-between full-width items-baseline"
  >
    <!-- TIMELINE DOT & THREAD -->
    <div
      style="
        position: absolute;
        left: -30px;
        top: 13px;
        height: 100%;
        width: 32px;
      "
    >
      <div class="column full-height">
        <div class="dot"></div>
        <div v-if="showThread" class="thread"></div>
      </div>
    </div>

    <!-- TIMESTAMP -->
    <q-item-section
      class="text-italic q-pr-sm"
      style="max-width: 200px"
    >
      {{ formattedTimestamp }}
    </q-item-section>

    <!-- EVENT TYPE -->
    <q-item-section class="text-h4 highlight text-uppercase">
      {{ $t(`events.${event.event_type}`) }}
    </q-item-section>

    <!-- EVENT USER -->
    <q-item-section class="col-auto">
      <BaseUserAvatar name_first :user="userData" />
    </q-item-section>
  </q-item>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import { capitalize } from '@/boot/filters';
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
</style>

<template>
  <!-- MOVEMENTS CALLOUT -->
  <div
    v-if="showMovementsCallout"
    class="col-auto row items-center q-my-sm movements-callout"
  >
    <div class="col text-body2">
      {{ $t('count_movements_since_last_count') }}
    </div>
    <div class="col-auto q-ml-sm">
      <q-btn
        flat
        dense
        round
        icon="mdi-history"
        :aria-label="$t('view_movements')"
        @click="movementsExpanded = !movementsExpanded"
      />
    </div>
  </div>

  <!-- MOVEMENTS DETAILS (EXPANDABLE AREA) -->
  <transition name="fade">
    <div
      v-if="movementsExpanded"
      class="col-auto q-mb-sm movements-panel scroll"
      style="max-height: 200px;"
    >
      <div
        v-if="loadingMovements"
        class="text-caption text-low q-pa-xs"
      >
        {{ $t('loading') }}
      </div>
      <div
        v-else-if="!movements.length"
        class="text-caption text-low q-pa-xs"
      >
        {{ $t('no_results') }}
      </div>
      <q-list
        v-else
        class="movements-list"
        dense
        separator
      >
        <q-item
          v-for="movement in movements"
          :key="movement._key || movement.id"
          class="movements-row"
        >
          <q-item-section class="text-caption">
            {{ formatMovementTimestamp(movement) }} → {{ movement.position_to_code }}
          </q-item-section>
          <q-item-section side class="text-caption text-low">
            <template v-if="displayMode === 'serial'">
              {{ movement.serial_code }}
            </template>
            <template v-else>
              {{ movement.qt_confirmed }}
            </template>
          </q-item-section>
        </q-item>
      </q-list>
    </div>
  </transition>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';

const { t: $t } = useI18n();
const movementsExpanded = ref(false);

function formatMovementTimestamp(movement) {
  const raw =
    movement?.end ||
    movement?.start ||
    movement?.created ||
    movement?.system_at ||
    null;

  if (!raw) {
    return '';
  }

  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) {
    return '';
  }

  return date.toLocaleString();
}
</script>

<style lang="scss" scoped>
.movements-callout {
  border-radius: 4px;
  padding: 4px 8px;
  background: rgba(255, 152, 0, 0.07);
  border: 1px solid rgba(255, 152, 0, 0.4);
}

.movements-panel {
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(0, 0, 0, 0.16);
}

.movements-scroll {
  max-height: 140px;
}

.movements-row {
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.movements-row:last-child {
  border-bottom: none;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

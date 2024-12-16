<template>
  <template v-if="results.length === 0">
      <q-space />
      <div v-if="filter.length === 0" class="col-auto q-mb-sm text-h1 item-center" style="width: 70%;">
        {{  $t('scan_start_position') }}
      </div>
      <div  v-else class="col-auto q-mb-sm text-h1 item-center" style="width: 70%;">
        {{  $t('no_results') }}
      </div>
    </template>

    <template v-else>

      <!-- PRODUCT LIST -->
      <div class="col-auto q-mb-sm text-h6">
        {{ $t(list_label) }} ({{ results.length }})
      </div>


      <div class="col scroll q-my-md column">
        <q-card
          v-for="item in results"
          :key="item.key"
          v-ripple
          bordered
          flat
          class="surface2 q-px-md q-py-md q-mb-sm"
          @click="selectItem(item)"
        >
          <div v-if="startFrom === 'serial'">
            <div class="text-h6 text-low">{{ item.product.code }}</div>
            <div class="text-body1 highlight">{{ item.code }}</div>
          </div>

          <div v-else>
            <div class="text-body1 highlight">{{ item.code }}</div>
          </div>
        </q-card>
      </div>

    </template>

    <q-space />

     <!-- PRODUCT SEARCH -->
    <SearchOrScan
      v-model="filter"
      @update:model-value="search"
    />

    <q-btn-toggle
      v-model="startFrom"
      @update:model-value="reset"
      spread
      unelevated
      toggle-color="theme-blue"
      color="blue-backdrop"
      :options="[
        { label: $t('position'), value: 'position' },
        { label: $t('serial'), value: 'serial' },
      ]"
    />
  </template>
<script setup>
</script>

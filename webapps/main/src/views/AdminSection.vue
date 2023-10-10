<template>
  <q-page-container class="absolute-full">
    <q-page class="q-px-md q-pb-md column full-height">
      <!-- TAB LINKS -->
      <q-tabs
        class="transparent text-low col-auto"
        active-class="text-high weight-bold"
        align="left"
        shrink
        dense
        indicator-color="primary">
        <q-route-tab
          v-for="(view, index) in admin_views"
          :key="index"
          :to="{ name: view }"
          class="display">
          {{ $t(`views.${view}`) }}
        </q-route-tab>
      </q-tabs>
      <q-card class="surface1 col" :style="`height: ${card_height}px`" square>
        <router-view v-slot="{ Component }" class="">
          <keep-alive>
            <component :is="Component" class="full-height" id="test" />
          </keep-alive>
        </router-view>
      </q-card>
    </q-page>
  </q-page-container>
</template>

<script>
export default {

  name: 'AdminSection',

  data () {
    return {
      current_view: 0,
      admin_views: [
        'userLibrary',
        'operationLibrary',
        'issueTypeLibrary',
        'formFieldLibrary',
        'flowLibrary',
        'printTemplateLibrary'
      ]
    }
  },
}
</script>

<style lang="css" scoped>
</style>

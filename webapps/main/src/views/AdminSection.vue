<template>
  <q-page-container>
    <q-page class="q-px-md q-pb-md">
      <!-- TAB LINKS -->
      <q-tabs
        class="transparent text-low"
        active-class="text-high weight-bold"
        align="left"
        shrink
        indicator-color="transparent">
        <q-route-tab
          v-for="(view, index) in admin_views"
          :key="index"
          :to="{ name: view }"
          class="display">
          {{ $t(`views.${view}`) }}
        </q-route-tab>
      </q-tabs>
      <q-card class="surface1" :style="`height: ${card_height}px`" square>
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
      ]
    }
  },

  computed: {
    card_height() {
     return this.$q.screen.height - 140
    }
  }
}
</script>

<style lang="css" scoped>
</style>

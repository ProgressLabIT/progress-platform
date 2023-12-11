<template>
  <v-card class="fill">
    <LoadingSignal v-if="!ready"></LoadingSignal>

    <v-row v-else class="fill-height">
      <v-col cols="2" class="fill-height d-flex flex-column">
        <v-tabs vertical background-color="transparent" color="white">
          <v-tab
            v-for="tab in sections"
            :key="tab"
            :to="{ name: tab }"
            class="menu display mb-2"
          >
            {{ $t(`views.${tab}`) }}
          </v-tab>
        </v-tabs>
      </v-col>

      <v-divider vertical></v-divider>

      <v-col>
        <router-view></router-view>
      </v-col>
    </v-row>
  </v-card>
</template>

<script>
import LoadingSignal from '@/components/LoadingSignal.vue';

export default {
  name: 'GeneralSettings',

  components: {
    LoadingSignal,
  },

  data() {
    return {
      ready: true,
      sections: ['companyDetails', 'defaultPhaseParams'],
    };
  },
};
</script>

<style lang="css" scoped>
.v-tab.menu {
  justify-content: flex-start;
}
</style>

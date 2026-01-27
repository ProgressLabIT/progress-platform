<template>
  <v-container class="fill-height">
    <v-row class="fill-height" align="center" justify="center">
      <v-col cols="auto" class="text-center">
        <h1 class="display highlight">{{ $t('oops_title') }}</h1>
        <p class="mb-6">{{ $t('alerts.404') }}</p>

        <v-btn
          v-for="link in links"
          :key="link"
          block
          class="mb-2"
          :color="$theme.blue"
          @click="$router.push({ name: link })"
        >
          {{ $t(`views.${link}`) }}
        </v-btn>
        <!-- <v-btn block :color="$theme.blue" @click="$router.push({name: 'productionOverview'})">
          Monitoraggio Produzione
        </v-btn> -->
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {
  name: 'NotFound',

  data() {
    return {
      links: ['warehouseRoot'],
    };
  },
};
</script>

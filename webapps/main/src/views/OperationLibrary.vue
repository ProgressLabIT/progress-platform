<template>
  <v-card class="fill">
    <LoadingSignal v-if="!vuex_ready" />

    <v-row v-else no-gutters class="fill-height">
      <v-col cols="3" class="fill-height d-flex flex-column">
        
          <!-- <h5>FILTRI</h5> -->
        <v-text-field
          class="px-5"
          append-icon="mdi-magnify"
          hide-details
          single-line
          clearable
          :label="$tc('search') | capitalize"
          v-model="search_text">
        </v-text-field>
          
          <v-row dense class="pt-6 flex-grow-0 text-uppercase">
            <v-col cols="8" class="pl-6 pb-1">
              <h6>{{ $tc('name') }}</h6>
            </v-col>
            <v-col cols="4">
              <h6>{{ $tc('code') }}</h6>
            </v-col>
          </v-row>

          <v-divider></v-divider>

          <div class="flex-grow-1 scroll" style="overflow-x: hidden">
            <v-row v-ripple dense
              v-for="(operation, index) in filtered_operations" :key="index"
              class="pointer"
              style="white-space: nowrap"
              :class="{ 'alternate-row': index % 2 == 0 }"
              :style="operation._key == selected_operation_key ? `background-color: ${$theme.blue_bg}` : '' "
              @click="showOperationDetail(operation)">
              <v-col cols="8" class="pl-6 pr-2 medium">
                {{ operation.name | capitalize }}
              </v-col>
              <v-col cols="4" class="medium">
                {{ operation.code }}
              </v-col>
            </v-row>
            <v-divider></v-divider>
            <v-row 
              align="center" 
              justify="center" 
              class="smaller py-2">
              {{ filtered_operations.length }} di {{ operation_list.length }}
            </v-row>
          </div>

        <v-spacer></v-spacer>
        
        <v-divider></v-divider>
        
        <v-btn :color="$theme.blue" class="ma-2" @click="openOperationNew">
          {{ $tc('operations.add_op') }}
        </v-btn>
      </v-col>

      <v-divider vertical></v-divider>

      <v-col class="fill-height scroll">
        <transition name="slide-fade" mode="out-in"> 
          <router-view
            :operation="getOperationData()" 
            :key="selected_operation_key">
          </router-view>
        </transition>
      </v-col>

    </v-row>

  </v-card>
</template>

<script>
import LoadingSignal from "@/components/LoadingSignal.vue"
import multiMatch from "@/lib/MultiFieldSearch.js"


export default {

  name: 'OperationLibrary',

  components: { LoadingSignal },

  data () {
    return {
      vuex_ready: false,
      search_text: undefined,
      selected_operation_key: undefined
    }
  },

  computed: {
    
    operation_list() {
      return this.$store.state.process.operations
    },

    filtered_operations() {
      const fields_to_search = ['name', 'code', 'description']
      return this.operation_list.filter( op => multiMatch(this.search_text, op, fields_to_search) )
    }
  },

  methods: {
    showOperationDetail(operation) {
      this.selected_operation_key = operation._key
      this.$router.push({
        name: 'operationDetail',
        params: { operation_key: this.selected_operation_key }
      })
    },

    getOperationData() {
      return this.operation_list.find( op => op._key == this.selected_operation_key )
    },

    openOperationNew() {
      this.$router.push({ name: 'operationNew' })
    }
  },

  created() {
    this.$store.dispatch('getOperations').then( () => this.vuex_ready = true )
  },
}
</script>

<style lang="css" scoped>
</style>
<template>
  <v-card class="fill">
    
    <LoadingSignal v-if="!vuex_ready" />

    <v-row v-else no-gutters class="fill-height">
      <v-col cols="3" class="fill-height d-flex flex-column">
        
        <div class="px-5">

          <BaseSearchBox :input.sync="search_text"></BaseSearchBox>
          

          <v-expansion-panels flat hover v-model="filter_panel" class="mt-2">
            <v-expansion-panel>
              <v-expansion-panel-header>
                <span v-if="filter_panel === undefined" class=" medium">
                  {{ $tc('user.more_filters') | capitalize }}
                </span>
                <span v-else class="medium">
                  {{ $tc('user.less_filters') | capitalize }}
                </span>
              </v-expansion-panel-header>
              <v-expansion-panel-content>
                <BaseAutocompleteDepartment 
                  @select="setDepartment($event)" 
                  class="pt-0 my-4"
                  text_classes="medium"
                  :label="$tc('department') | capitalize">
                </BaseAutocompleteDepartment>

            
                <v-row dense class="mt-6"> 
                  <v-col v-for="(check, index) in bool_filters" 
                  :key="index">
                    <v-checkbox 
                      dense
                      hide-details
                      class="ma-0 pa-0"
                      v-model="check.value">
                      <template v-slot:label>
                        <span class="medium">
                          {{ $tc(`user.${check.name}`) | capitalize }}
                        </span>
                      </template>
                    </v-checkbox>
                  </v-col> 
                </v-row>
              </v-expansion-panel-content>
            </v-expansion-panel>
          </v-expansion-panels>  
        </div>

          <v-row dense class="pt-2 flex-grow-0 text-uppercase">
            <v-col cols="6" class="pl-6 pb-1">
              <h6>{{ $tc('name') }}</h6>
            </v-col>
            <v-col cols="6">
              <h6>{{ $tc('user.surname') }}</h6>
            </v-col>
          </v-row>

          <v-divider></v-divider>

          <div class="flex-grow-1 scroll" style="overflow-x: hidden">
            <v-row v-ripple dense
              v-for="(user, index) in filtered_users" :key="index"
              class="pointer"
              style="white-space: nowrap"
              :class="{ 'alternate-row': index % 2 == 0 }"
              :style="user._key == selected_user_key ? `background-color: ${$theme.blue_bg}` : '' "
              @click="showUser(user)">
              <v-col cols="6" class="pl-6 pr-2 medium">
                {{ user.name }}
              </v-col>
              <v-col cols="6" class="medium">
                {{ user.surname }}
              </v-col>
            </v-row>
            <v-divider></v-divider>
            <v-row 
              align="center" 
              justify="center" 
              class="smaller py-2">
              {{ filtered_users.length }} {{ $tc('of') }} {{ user_list.length }}
            </v-row>
          </div>

        <v-spacer></v-spacer>
        
        <v-divider></v-divider>
        
        <v-btn :color="$theme.blue" class="ma-2" @click="openUserNew">
          {{ $tc('user.add') }}
        </v-btn>
      </v-col>

      <v-divider vertical></v-divider>

      <v-col class="fill-height scroll">
        <transition name="slide-fade" mode="out-in"> 
          <!-- <UserInfoScreen  -->
          <router-view
            :user="getUserData()" 
            :key="selected_user_key">
          </router-view>
          <!-- </UserInfoScreen> -->
        </transition>
      </v-col>

    </v-row>

  </v-card>
</template>

<script>
// import axios from 'axios'
import BaseSearchBox from "@/components/BaseSearchBox"
import LoadingSignal from "@/components/LoadingSignal.vue"
import BaseAutocompleteDepartment from "@/components/BaseAutocompleteDepartment.vue"
// import UserInfoScreen from "@/components/UserInfoScreen.vue"
import multiMatch from "@/lib/MultiFieldSearch.js"


export default {

  name: 'UserLibrary',

  components: { 
    // UserInfoScreen,
    BaseSearchBox,
    BaseAutocompleteDepartment,
    LoadingSignal
  },

  data() {
    return {
      vuex_ready: false,
      user_index: 0,
      search_text: '',
      department_filter: null,
      // selected_user_key: null,
      bool_filters: [
        { name: 'enabled', value: true },
        { name: 'disabled', value: true },
        { name: 'logged_in', value: true },
        { name: 'logged_out', value: true }
      ],
      filter_panel: undefined,
    }
  },

  computed: {
    user_list() {
      return this.$store.state.user.user_list
    },

    selected_user_key() {
      return this.$route.params.user_key
    },

    filtered_users() {
      const dep_filter = this.department_filter
      const list = this.user_list.filter( user => {
        
        const u_dep = user.department  
        let department_match = true

        if (dep_filter) {
          if (u_dep) {
            // Selected users with no department assigned
            // Filter out all users that have a department
            if (dep_filter != u_dep._key) department_match = false
          }
          else {
            // Filter out users with department different from the one selected
            if (dep_filter != 'none') department_match = false
          }
        }
          
        const user_match = this.search_text
          ? multiMatch(this.search_text, user, ['name', 'surname', 'username', 'email'])
          : true


        let match_map = this.bool_filters.map( filter => {
          let bool_match = true

          if (
            !filter.value && (
            (filter.name == 'enabled' && user.active)
            || (filter.name == 'disabled' && !user.active)
            || (filter.name == 'logged_in' && user.logged_in)
            || (filter.name == 'logged_out' && !user.logged_in)
            )
          ) bool_match = false

          return bool_match
        })

        return department_match && user_match && !match_map.some( _ => _ === false )
      })

      return list
    },

  },

  methods: {
    setDepartment(event) {
      this.department_filter = event
    },

    showUser(user) {
      this.selected_user_key = user._key
      this.$router.push({ 
        name: 'userInfo', 
        params: { user_key: user._key }
      })
    },

    getUserData() {
      return this.user_list.find( user => user._key === this.selected_user_key)
    },

    openUserNew() {
      this.$router.push({ name: 'newUser' })
    }
  },

  created() {
    this.$store.dispatch('loadUsers').then(() => {
      this.vuex_ready = true
    })
  }
}
</script>

<style lang="css" scoped>
.v-expansion-panel-header {
  padding: 0px;
}

.v-expansion-pane-content__wrap {
  padding: 0px;
}
</style>  

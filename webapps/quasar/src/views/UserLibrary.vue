<template>
  <LoadingSignal v-if="!vuex_ready" />

  <div class="row full-height">
    <div class="col-3 full-height column">

      <q-input
        dense
        class="q-px-lg q-py-sm"
        :placeholder="$capitalize($t('search'))"
        v-model="search_text">
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>

      <q-expansion-item
        v-model="filter_panel"
        :label="filters_label"
        header-class="q-px-lg">
        <div class="row q-col-gutter-md q-pa-lg">
          <div
            class="col-6"
            v-for="(check, index) in bool_filters"
            :key="index">
            <q-checkbox
              dense
              size="xs"
              v-model="check.value">
                <span class="medium">
                  {{ $capitalize($t(`user.${check.name}`)) }}
                </span>
            </q-checkbox>
          </div>
        </div>
      </q-expansion-item>

      <!-- USER LIST HEADERS -->
      <div class="row q-mt-md q-px-lg q-py-sm text-h6 text-uppercase weight-bold">
        <div class="col-6">
          {{ $t('name') }}
        </div>
        <div class="col-6">
          {{ $t('user.surname') }}
        </div>
      </div>

      <q-separator />

      <!-- USER LIST -->
      <div class="scroll col">
        <div
          class="row pointer q-px-lg q-py-xs medium"
          :class="{ 'alternate-row': index % 2 == 0, 'bg-blue-backdrop': user._key == selected_user_key }"
          v-for="(user, index) in filtered_users"
          :key="index"
          style="white-space: nowrap;"
          @click="showUser(user)">
          <div class="col-6">
            {{ user.name }}
          </div>
          <div class="col-6">
            {{ user.surname }}
          </div>
        </div>
      </div>

      <q-separator />

      <!-- USER LIST COUNT -->
      <div class="row flex-center smaller q-py-xs">
        {{ filtered_users.length }} {{ $t('of') }} {{ user_list.length }}
      </div>

      <div class="q-pa-md q-mt-auto">
        <q-btn
          class="full-width q-mt-auto"
          color="theme-blue"
          :label="$t('user.add')"
          @click="openUserNew">
        </q-btn>
      </div>

    </div>

    <q-separator vertical />

    <!-- USER DATA -->
    <div class="col">
      <router-view v-slot="{ Component, route }">
        <transition name="slide-fade" mode="out-in">
          <div :key="route.fullPath">
            <component
              :is="Component"
              :user="getUserData()"
              :key="selected_user_key">
            </component>
          </div>
        </transition>
      </router-view>
    </div>
  </div>
</template>

<script>
// import axios from 'axios'
import LoadingSignal from "@/components/LoadingSignal.vue"
import BaseAutocompleteDepartment from "@/components/BaseAutocompleteDepartment.vue"
// import UserInfoScreen from "@/components/UserInfoScreen.vue"
import multiMatch from "@/lib/MultiFieldSearch.js"


export default {

  name: 'UserLibrary',

  components: { 
    // UserInfoScreen,
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

    filters_label() {
      const string = this.filter_panel
        ? 'user.less_filters'
        : 'user.more_filters'
      return this.$capitalize(this.$t(string))
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

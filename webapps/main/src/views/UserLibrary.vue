<template>
  <LoadingSignal v-if="!vuex_ready" />

  <q-splitter v-else v-model="splitter_model" class="absolute-full">
    <template #before>
      <div class="full-height column">
        <q-input
          v-model="search_text"
          dense
          filled
          class="q-px-md q-pt-md"
          :placeholder="$capitalize($t('search'))"
        >
          <template #append>
            <q-icon name="mdi-magnify" />
          </template>
        </q-input>

        <q-expansion-item
          v-model="filter_panel"
          :label="filters_label"
          header-class="q-px-lg"
        >
          <div class="row q-col-gutter-md q-pa-lg">
            <div
              v-for="(check, index) in bool_filters"
              :key="index"
              class="col-6"
            >
              <q-checkbox v-model="check.value" dense size="xs">
                <span class="medium">
                  {{ $capitalize($t(`user.${check.name}`)) }}
                </span>
              </q-checkbox>
            </div>
          </div>
        </q-expansion-item>

        <!-- USER LIST HEADERS -->
        <div
          class="row q-mt-md q-px-lg q-py-sm text-h6 text-uppercase weight-bold"
        >
          <div class="col-1"></div>
          <div class="col-5 ellipsis">
            {{ $t('name') }}
          </div>
          <div class="col-5 ellipsis">
            {{ $t('user.surname') }}
          </div>
        </div>

        <q-separator />

        <!-- USER LIST -->
        <q-scroll-area class="col">
          <div
            v-for="(user, index) in filtered_users"
            :key="index"
            class="row pointer q-px-lg q-py-xs medium overflow-hidden"
            :class="{
              'alternate-row': index % 2 === 0,
              'bg-blue-backdrop': user._key === selected_user_key,
            }"
            @click="showUser(user)"
          >
            <div class="col-1">
              <q-icon :name="getActiveIcon(user.active)" />
            </div>
            <div class="col-5 ellipsis">
              {{ user.name }}
            </div>
            <div class="col-5 ellipsis">
              {{ user.surname }}
            </div>
          </div>
        </q-scroll-area>

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
            @click="openUserNew"
          >
          </q-btn>
        </div>
      </div>
    </template>

    <template #after>
      <!-- USER DATA -->
      <div class="col full-height">
        <router-view v-slot="{ Component, route }">
          <component
            :is="Component"
            v-if="route.name === 'userLibrary' || route.name === 'newUser'"
          />
          <component
            :is="Component"
            v-else-if="selected_user"
            :operation="selected_user"
            :user="selected_user"
          />
        </router-view>
      </div>
    </template>
  </q-splitter>
</template>

<script>
// import axios from 'axios'
import LoadingSignal from '@/components/LoadingSignal.vue';
// import UserInfoScreen from "@/components/UserInfoScreen.vue"
import multiMatch from '@/lib/MultiFieldSearch.js';

export default {
  name: 'UserLibrary',

  components: {
    // UserInfoScreen,
    LoadingSignal,
  },

  data() {
    return {
      vuex_ready: false,
      user_index: 0,
      search_text: '',
      department_filter: null,
      bool_filters: [
        { name: 'enabled', value: true },
        { name: 'disabled', value: true },
      ],
      filter_panel: undefined,
      splitter_model: 30,
    };
  },

  computed: {
    user_list() {
      return this.$store.state.user?.user_list;
    },

    filters_label() {
      const string = this.filter_panel
        ? 'user.less_filters'
        : 'user.more_filters';
      return this.$capitalize(this.$t(string));
    },

    selected_user_key() {
      return this.$route.params.user_key;
    },

    selected_user() {
      return this.user_list.find(
        (user) => user._key === this.selected_user_key,
      );
    },

    filtered_users() {
      const dep_filter = this.department_filter;
      const list = this.user_list.filter((user) => {
        const u_dep = user.department;
        let department_match = true;

        if (dep_filter) {
          if (u_dep) {
            // Selected users with no department assigned
            // Filter out all users that have a department
            if (dep_filter != u_dep._key) {
              department_match = false;
            }
          } else {
            // Filter out users with department different from the one selected
            if (dep_filter != 'none') {
              department_match = false;
            }
          }
        }

        const user_match = this.search_text
          ? multiMatch(this.search_text, user, [
              'name',
              'surname',
              'username',
              'email',
            ])
          : true;

        let match_map = this.bool_filters.map((filter) => {
          let bool_match = true;

          if (
            !filter.value &&
            ((filter.name == 'enabled' && user.active) ||
              (filter.name == 'disabled' && !user.active) ||
              (filter.name == 'logged_in' && user.logged_in) ||
              (filter.name == 'logged_out' && !user.logged_in))
          ) {
            bool_match = false;
          }

          return bool_match;
        });

        return (
          department_match && user_match && !match_map.some((_) => _ === false)
        );
      });

      return list;
    },
  },

  created() {
    const active_only = false;
    this.$store.dispatch('loadUsers', active_only).then(() => {
      this.vuex_ready = true;
    });
  },

  methods: {
    setDepartment(event) {
      this.department_filter = event;
    },

    showUser(user) {
      this.$router.push({
        name: 'userInfo',
        params: { user_key: user._key },
      });
    },

    openUserNew() {
      this.$router.push({ name: 'newUser' });
    },
    getActiveIcon(active) {
      return active ? 'mdi-account' : 'mdi-account-cancel-outline';
    },
  },
};
</script>

<style lang="css" scoped>
.v-expansion-panel-header {
  padding: 0px;
}

.v-expansion-pane-content__wrap {
  padding: 0px;
}
</style>

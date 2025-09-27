<template>
  <div class="column q-px-md fit q-col-gutter-md">
    <!-- HEADER -->
    <div class="row items-center">
      <div
        class="text-h3 display highlight col-auto hover-underline q-mr-md"
        @click="goToProductPage"
      >
        {{ serial?.product?.code }}
      </div>
      <div
        v-if="!(edit_mode && can_edit && config.allowSerialCodeEdit)"
        class="text-h4 col-auto text-uppercase"
      >
        {{ ' # ' + serial?.code }}
      </div>
      <q-input
        v-else
        :model-value="serial?.code"
        dense
        filled
        :label="$t('serial.code')"
        class="input-uppercase"
        @update:model-value="(v) => (serial.code = v.toUpperCase())"
      >
      </q-input>

      <q-space></q-space>

      <q-chip
        :color="serialAvailable ? 'theme-green' : 'theme-grey'"
        class="smaller text-uppercase highlight">
        {{ serialAvailable ? $t('available') : $t('unavailable') }}
      </q-chip>

      <q-btn
        v-if="printAvailable"
        flat
        round
        icon="mdi-printer"
        class="q-ml-sm"
        @click.stop="openPrintDialog"
      >
        <q-tooltip>{{ $capitalize($t('print')) }}</q-tooltip>
      </q-btn>
    </div>

    <!-- SUB HEADER 1 - SERIAL CREATION -->
    <div class="row q-col-gutter-x-lg items-center text-h6">
      <div class="col-auto text-h5 text-low text-uppercase">
        {{ $t('creation_date') }}
      </div>
      <div class="col-auto">{{ serialTimeString(serial?.created) }}</div>
      <div class="col-auto row items-center">
        <BaseUserAvatar
          :user="$store.getters.user_data(serial?.user_key)"
          size="24px"
          class="q-ml-md"
        />
      </div>
    </div>

    <!-- SUB HEADER 2 - SERIAL RELEASE -->
    <div class="row q-col-gutter-x-lg items-center text-h6">
      <div class="col-auto text-h5 text-low text-uppercase">
        {{ $t('release_date') }}
      </div>
      <div class="col-auto">{{ serialTimeString(serial?.released) }}</div>
    </div>

    <!-- SUB HEADER 3 - SERIAL RELEASE -->
    <div class="row q-col-gutter-x-lg items-center text-h6">
      <div class="col-auto text-h5 text-low text-uppercase">{{ $t('work_order.long').toUpperCase() }}</div>
      <div class="col-auto hover-underline" @click="goToWorkOrderPage">
        {{ serial?.wo_code }}
      </div>
    </div>


    <!-- SERIAL DATA -->
    <q-tabs
      v-model="tab"
      dense
      class="q-mt-lg text-low"
      content-class="text-h5"
      indicator-color="theme-blue"
      align="left"
      active-class="text-high weight-bold"
    >
      <q-tab name="form" :label="$t('serial_data')" class="text-left" />
      <q-tab name="history" :label="$t('history')" />
    </q-tabs>

    <q-card square class="col surface2 scroll">
      <q-tab-panels v-model="tab" class="transparent">
        <!-- SERIAL FORM DATA -->
        <q-tab-panel name="form">
          <template v-if="serial?.data?.length > 0">
            <div class="column col scroll q-pt-sm q-gutter-y-md">
              <div
                v-for="field in serial?.data"
                :key="field?.form_field_key"
                class="row q-col-gutter-x-md items-center"
              >
                <FormField
                  :field="field"
                  :root-path="`/media/serial/${serial_key}/${field?.form_field_key}`"
                  :disable="!(edit_mode && can_edit)"
                  class="col"
                  dense
                  @update="field.value = $event"
                />
                <q-icon
                  v-if="field.last_updated"
                  class="col-auto"
                  name="mdi-information-outline"
                  color="theme-grey"
                  size="24px"
                >
                  <q-tooltip
                    anchor="center left"
                    self="center right"
                    delay="200"
                    class="bg-theme-blue">
                    <div class="column q-gutter-y-xs text-right q-pa-sm" >
                      <div class="text-h5">
                        {{ $t('last_update') }}
                      </div>
                      <BaseUserAvatar
                      :user="getFieldUser(field)"
                      size="24px"
                      />
                      <div class="text-h6 text-low">{{ getFieldTimestamp(field) }}</div>
                    </div>
                  </q-tooltip>
                </q-icon>
              </div>
            </div>
          </template>
          <div v-else class="col-auto text-italic">No data</div>
        </q-tab-panel>

        <!-- EVENTS -->
        <q-tab-panel name="history">
          <q-list class="col q-pb-lg">
            <TimelineItem
              v-for="(e, index) in history"
              :key="e._key"
              :event="e"
              :show-thread="index < history.length - 1"
              :user-data="getUserData(e)"
            />
          </q-list>
        </q-tab-panel>
      </q-tab-panels>
    </q-card>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia';
import { ref, computed, onBeforeUnmount, onMounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter, useRoute } from 'vue-router';
import { useStore } from 'vuex';
import { api as $api } from '@/boot/axios';
import { capitalize } from '@/boot/filters';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import FormField from '@/components/FormField.vue';
import TimelineItem from '@/components/TimelineItem.vue';
import { formatDateTime } from '@/lib/TimeHandling';
import { usePrintDialog } from '@/lib/print';
import { useConfigStore } from '@/stores/config';

const props = defineProps({
  // from router
  serial_key: {
    type: String,
    required: true,
  },
  edit_mode: {
    type: Boolean,
    required: true,
  },
});

defineEmits(['exit']);

// Store and router setup
const store = useStore();
const router = useRouter();
const route = useRoute();
const { t:$t, locale } = useI18n();

// Config store
const { config } = storeToRefs(useConfigStore());

// Print dialog
const { open: openPrintDialog, isAvailable: printAvailable } = usePrintDialog({
  context: 'serial',
  contextData: props.serial_key,
});

// Reactive data
const tab = ref('form');
const history = ref([]);
const base_path = ref('/media/user/');
const events = ref(null);
const serialAvailable = ref(false);

// Computed properties
const serial = computed(() => store.getters.getSerialData(props.serial_key));

const serialTimeString = (isoString) => {
  const config = {
    year: '2-digit',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  };
  return capitalize(formatDateTime(isoString, locale.value, config));
};

const can_edit = computed(() => !store.getters.getSerialData(props.serial_key).deleted);

// Methods
const getInfo = () => {
  // Get history
  $api
    .get('event', { params: { serial_key: props.serial_key } })
    .then((resp) => (history.value = resp.data));

  // Get inventory availability
  const params = new URLSearchParams();
  params.append('serial_keys', props.serial_key);
  $api.get('inventory', { params })
    .then((resp) => {
      serialAvailable.value = resp.data.length > 0;
    })
    .catch((err) => {
      console.log(err.response.data.message);
    });
};

const handleMessage = (message) => {
  let event = JSON.parse(message.data);
  if (event?.serial_key === props.serial_key) {
    getInfo();
  }
};

const getAvatarSrc = (user) => {
  return base_path.value + (user.name + user.surname).replace(/\s+/g, '') + '.jpg';
};

const getUserData = (event) => {
  const user = store.getters.user_data(event.user_key);
  return {
    ...user,
    full_name: user.name + ' ' + user.surname,
    src: getAvatarSrc(user),
  };
};

const getHumanDate = (timestamp) => {
  const config = {
    year: '2-digit',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
    weekday: 'short',
  };
  return capitalize(formatDateTime(timestamp, locale.value, config));
};

const goToWorkOrderPage = () => {
  router.push({
    name: 'workOrderScreen',
    params: {
      wo_key: serial.value.wo_key,
    },
    query: {
      back_to: route.name,
      ...route.query,
    },
  });
};

const goToProductPage = () => {
  router.push({
    name: 'productHome',
    params: {
      product_key: serial.value.product_key,
    },
  });
};

const getFieldUser = (field) => {
  const userKey = history.value.find((e) => e._key === field.last_updated)?.user_key;
  return store.getters.user_data(userKey);
};

const getFieldTimestamp = (field) => {
  const timestamp = history.value.find((e) => e._key === field.last_updated)?.timestamp;
  return getHumanDate(timestamp, {
    year: '2-digit',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// Watchers and lifecycle hooks
watch(() => props.serial_key, () => {
  getInfo();
}, { immediate: true });

onMounted(() => {
  store.dispatch('loadUsers');
  getInfo();
  let eventURL = $api.defaults.baseURL + '/notification/serial-notification';
  events.value = new EventSource(eventURL, {
    withCredentials: false,
  });
  events.value.addEventListener('serial-notification', (event) => {
    handleMessage(event);
  });
});

onBeforeUnmount(() => {
  if (events.value) {
    events.value.close();
  }
});
</script>

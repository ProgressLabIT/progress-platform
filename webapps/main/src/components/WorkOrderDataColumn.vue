<template>
  <div class="q-px-lg q-py-md full-height column">
    <!-- COLUMN HEADER -->
    <div class="text-uppercase low-text text-h5 q-mb-xs">
      {{ $t('work_order.wo_code') }}
    </div>
    <div class="row">
      <div class="col display weight-bold text-h3 ellipsis">
        {{ wo_data.wo_code }}
      </div>
      <div class="col-auto">
        <q-btn
          v-if="printDialogAvailable"
          flat
          round
          icon="mdi-printer"
          style="margin-top: -10px; margin-right: -10px"
          @click.stop="openPrintDialog"
        >
          <q-tooltip>{{ $capitalize($t('print')) }}</q-tooltip>
        </q-btn>
      </div>
    </div>

    <div class="text-uppercase low-text text-h5 q-mb-xs q-mt-lg">
      {{ $t('project') }}
    </div>
    <div class="full-width display weight-bold text-h3 ellipsis">
      {{ wo_data.project_code }}
    </div>

    <div class="row justify-between text-uppercase low-text q-mt-lg text-h5">
      <div>{{ $t('product.label') }}</div>
      <div>{{ $t('quantity.short') }}</div>
    </div>

    <div class="row justify-between q-mt-xs">
      <div class="col-9">
        <div
          class="text-truncate display text-h3"
          :class="{ 'hover-link': user_can_access_library }"
          @click="user_can_access_library ? goToProductPage() : null">
          {{ wo_data.product_code }}
        </div>
        <div class="medium q-mt-xs">
          {{ wo_data.product_description }}
        </div>
      </div>
      <div class="col-auto display text-h3">
        {{ wo_data.qt_planned }}
      </div>
    </div>

    <div
      class="row justify-between items-end weight-bold text-uppercase q-mt-md q-mb-xs"
    >
      <div class="low-text text-h5">
        {{ $t('progress') }}
      </div>
      <div class="text-h3">{{ wo_data.progress }}%</div>
    </div>

    <BaseProgressBar :data="wo_data" class="q-mt-sm" />

    <!-- INFO PANELS -->
    <div id="panels" class="row q-mt-lg justify-between text-h6 text-uppercase">
      <div
        v-for="tab in views"
        :key="tab.name"
        style="cursor: pointer"
        :class="current_view === tab.name ? 'weight-bold' : 'low-text'"
        @click="current_view = tab.name"
      >
        {{ tab.text }}
      </div>
    </div>

    <q-tab-panels
      v-model="current_view"
      animated
      class="transparent q-mt-lg col column"
    >
      <!-- WORK ORDER DETAILS -->
      <q-tab-panel name="info" class="q-pa-none col">
        <div
          v-for="i in wo_info"
          :key="i.name"
          class="row justify-between items-end q-mb-sm text-high"
        >
          <div class="text-uppercase text-caption">
            {{ i.text }}
          </div>
          <div class="weight-medium text-body1 relative-position">
            <q-icon
              v-if="
                isLate(wo_data.due_by) &&
                i.name === 'due_by' &&
                wo_data.status !== 'closed'
              "
              class="q-mb-xs q-mr-xs"
              name="mdi-alert-octagon"
              color="theme-red"
            >
            </q-icon>
            {{ $capitalize(woInfoValue(i.name)) }}
          </div>
        </div>
      </q-tab-panel>

      <!-- ASSIGNMENTS -->
      <q-tab-panel name="people" class="q-pa-none column col">
        <div class="col-11 scroll">
          <BaseUserAvatar
            v-for="operator in assignments"
            :key="operator._key"
            :user="operator"
            name_class="highlight text-body1"
            class="q-mb-md q-py-xs"
            size="40px"
          >
            <template #subtitle>
              <div class="text-low low-text">
                {{ $capitalizeAll(getAssignedPhases(operator)) }}
              </div>
            </template>
          </BaseUserAvatar>
        </div>

        <q-space />

        <div class="col-auto text-uppercase text-caption">
          {{ $t('job.unassigned_jobs') }}: {{ unassigned_jobs.length }}
        </div>
      </q-tab-panel>
    </q-tab-panels>

    <!-- ACTIONS -->
    <q-btn
      v-if="wo_data.status !== 'closed'"
      outline
      square
      class="full-width q-mt-md"
      color="theme-blue"
      :loading="saving"
      :label="$t('update')"
    >
      <ProductionAdminMenu :wo="wo_data" show-work-order-actions/>
    </q-btn>

  </div>
</template>

<script>
import { DateTime as DT } from 'luxon';
import BaseProgressBar from '@/components/BaseProgressBar.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import { durationFromMillisec } from '@/lib/duration.js';
import { getPicPath } from '@/lib/media.js';
import { formatDateTime } from '../lib/TimeHandling';
import { usePrintDialog } from '@/lib/print';
import ProductionAdminMenu from '@/components/ProductionAdminMenu.vue';

export default {
  name: 'WorkOrderDataColumn',

  components: {
    BaseProgressBar,
    BaseUserAvatar,
    ProductionAdminMenu,
  },

  props: {
    wo_data: {
      type: Object,
      required: true,
    },
  },

  setup(props) {
    const { open, isAvailable } = usePrintDialog({
      context: 'workorder',
      contextData: {
        ...props.wo_data,
      },
    });

    return {
      openPrintDialog: open,
      printDialogAvailable: isAvailable
    }
  },

  data() {
    return {
      current_view: 'info',
      edit_project: false,
      temp_project_code: null,
      edit_qt: false,
      new_qt: null,
      edit_date: null,
      temp_date: null,
      show_job_qt_rebalance: false,
      delete_stage: null,
      saving: false,
    };
  },

  computed: {
    views() {
      return [
        {
          name: 'info',
          text: this.$t('info'),
          class: 'justify-start',
        },
        {
          name: 'people',
          text: this.$t('people') + ' (' + this.people_count + ')',
          class: 'justify-end',
        },
        // { name: 'equipment', text: 'MACCHINARI', align: 'end' },
      ];
    },

    wo_info() {
      return [
        {
          name: 'status',
          text: this.$t('status'),
        },
        {
          name: 'created',
          text: this.$t('creation_date'),
          value: '',
        },
        {
          name: 'start_from',
          text: this.$t('start_from_date'),
        },
        {
          name: 'start',
          text: this.$t('start_date'),
        },
        {
          name: 'due_by',
          text: this.$t('due_by'),
        },
        // { name: 'queueing_time', text: 'T. coda' },
        {
          name: 'end',
          text: this.$t('end_date'),
        },
        {
          name: 'processing_time',
          text: this.$t('processing_time'),
        },
        {
          name: 'processing_cost',
          text: this.$t('processing_cost'),
        },
        // {
        //   name: 'material_cost',
        //   text: this.$t('material_cost')
        // },
        // {
        //   name: 'total_cost',
        //   text: this.$t('total_cost')
        // },
      ];
    },

    user_can_access_library() {
      return this.$store.state.session.scope.includes('library')
    },

    assignments() {
      // handle missing data gracefully
      if (typeof this.wo_data != 'undefined') {
        const assignments = {};

        this.wo_data.jobs.forEach((j) => {
          if (j.assigned_to != null) {
            const key = j.assigned_to._key;
            if (key in assignments) {
              assignments[key].jobs.push(j);
            } else {
              const data = {
                ...this.$store.getters.user_data(key),
                jobs: [j],
              };
              assignments[key] = data;
            }
          }
        });
        return assignments;
      } else {
        return {};
      }
    },

    people_count() {
      return Object.keys(this.assignments).length;
    },

    unassigned_jobs() {
      let unassigned_jobs = [];
      if (typeof this.wo_data != 'undefined') {
        unassigned_jobs = this.wo_data.jobs.filter(
          (j) => j.assigned_to == null,
        );
      }
      return unassigned_jobs;
    },

    min_allowable_wo_qt() {
      return Math.max(
        this.wo_data.jobs.map((j) => j.qt_completed + j.active_batch_qt),
      );
    },
  },

  methods: {
    woInfoValue(info_name) {
      switch (info_name) {
        case 'status': {
          if (this.wo_data.status == 'closed') {
            return this.$t('closed');
          } else {
            let active_text = this.$t('active');
            let inactive_text = ['created', 'planned'].includes(
              this.wo_data.status,
            )
              ? this.$t('production.filters.queued')
              : this.$t('waiting');
            // let on_time_text = this.$t('on_time')
            // let late_text = this.$t('late')
            // let critical_text = this.$t('critical')
            let active = this.wo_data.active ? active_text : inactive_text;

            /*
            let state = ''

            if (this.wo_data.critical) state = critical_text
            else if (!this.wo_data.on_time) state = late_text
            else state = on_time_text
            */
            return active; //+ ' - ' + state
          }
        }

        case 'created':
        case 'start_from':
        case 'due_by': {
          const value = this.wo_data[info_name];
          if (!value) {
            return '-';
          }

          return formatDateTime(value, this.$i18n.locale, {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: '2-digit',
          });
        }

        case 'start':
        case 'end': {
          const value = this.wo_data[info_name];
          if (!value) {
            return '-';
          }

          return formatDateTime(value, this.$i18n.locale, {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: '2-digit',
            hour: 'numeric',
            minute: 'numeric',
          });
        }

        case 'processing_time': {
          const processing_time = this.wo_data.processing_time;
          return processing_time
            ? durationFromMillisec(processing_time, { precision: 's' })
            : '-';
        }

        case 'queueing_time': {
          const created = DT.fromISO(this.wo_data.created);
          const start = DT.fromISO(this.wo_data.start);
          const benchmark = start ? start : DT.utc();
          return this.wo_data.start
            ? durationFromMillisec(benchmark - created, { precision: 'h' })
            : '-';
        }

        case 'processing_cost': {
          return (this.wo_data.processing_cost || 0).toFixed(2) || '-';
        }

        case 'material_cost': {
          return (this.wo_data.material_cost || 0).toFixed(2) || '-';
        }

        case 'total_cost': {
          return (this.wo_data.total_cost || 0).toFixed(2) || '-';
        }
      }
    },

    isLate(due_by_date) {
      return DT.fromISO(due_by_date) < DT.now();
    },

    getPicPath(operator) {
      return getPicPath(operator);
    },

    getAssignedPhases(operator) {
      let phase_list = operator.jobs.map((j) => j.phase_alias);
      return phase_list.join(' / ');
    },

    panelHeight() {
      let height = document.body.clientHeight - 360;
      return height + 'px';
    },

    goToProductPage() {
      this.$router.push({
        name: 'productHome',
        params: {
          product_key: this.wo_data.product_key,
        },
      });
    }
  },
};
</script>

<style lang="scss">
#panels div:hover {
  text-decoration: underline;
}
</style>

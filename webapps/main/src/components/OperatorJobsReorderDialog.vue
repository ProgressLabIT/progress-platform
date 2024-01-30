<template>
  <!-- TODO: Create a better base component for using with custom dialog plugin components -->
  <BaseDialog
    :show="true"
    :get-dialog-ref="getDialogRef"
    @close="onDialogHide"
    @show="onShow"
    @hide="onHide"
  >
    <q-card class="reorder-dialog-card">
      <q-card-section class="display q-px-lg q-pt-lg">
        {{ operator.name }} {{ operator.surname }}
      </q-card-section>

      <q-card-section>
        <q-markup-table class="draggable-table">
          <thead>
            <tr>
              <th align="left">#</th>
              <th align="left">
                {{ $t('work_order.list_headers.sequence').toUpperCase() }}
              </th>
              <th align="left">{{ $t('work_order.wo_code').toUpperCase() }}</th>
              <th align="left">{{ $t('project').toUpperCase() }}</th>
              <th align="left">{{ $t('product.label', 1).toUpperCase() }}</th>
              <th align="left">{{ $t('phase.short').toUpperCase() }}</th>
              <th align="left">
                <q-icon name="mdi-flag" />
              </th>
              <th align="left">
                {{ $t('quantity.completed.short').toUpperCase() }}
              </th>
              <th align="left">
                {{ $t('quantity.planned.short').toUpperCase() }}
              </th>
              <th align="left">
                {{ $t('production.filters.ready').toUpperCase() }}
              </th>
              <th align="right">
                {{ $t('work_order.list_headers.due_by').toUpperCase() }}
              </th>
            </tr>
          </thead>

          <!--
            Using v-once as Vue doesn't need to render anything else since we don't care about reactivity.
            Furthermore, SortableJS may interfere with Vue's rendering and cause issues.
          -->
          <tbody
            v-for="({ workOrderKey, jobs }, groupIndex) in jobsByWorkOrder"
            :key="workOrderKey"
            class="draggable"
          >
            <tr v-for="(job, index) in jobs" :key="job._key">
              <template v-if="index === 0">
                <td :rowspan="jobs.length">
                  {{ groupIndex + 1 }}
                </td>
                <td :rowspan="jobs.length">
                  {{ job.wo_sequence }}
                </td>
                <td :rowspan="jobs.length">
                  {{ job.wo_code }}
                </td>
                <td :rowspan="jobs.length">
                  {{ job.project_code }}
                </td>
                <td :rowspan="jobs.length">
                  {{ job.product_code }}
                </td>
              </template>

              <td>{{ job.phase_alias }}</td>
              <td>{{ job.issues_open ?? 0 }}/{{ job.issues_total ?? 0 }}</td>
              <td>
                {{ job.qt_completed }}
              </td>
              <td>
                {{ job.qt_planned }}
              </td>
              <td>
                <q-icon :name="jobIcon(job).name" :color="jobIcon(job).color" />
              </td>
              <td align="right">
                <div class="row items-center justify-end q-gutter-xs">
                  <q-icon
                    v-if="job.due_by && job.due_by < new Date().toISOString()"
                    color="theme-red"
                    name="mdi-alert-octagon"
                  />
                  <div>
                    {{
                      job.due_by === null
                        ? '-'
                        : $shortDateString(job.due_by, $i18n.locale)
                    }}
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </q-markup-table>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn
          :label="$t('cancel')"
          color="theme-grey"
          @click="onDialogCancel"
        />

        <q-btn :label="$t('save')" color="primary" @click="save" />
      </q-card-actions>
    </q-card>
  </BaseDialog>
</template>

<script setup>
import { useDialogPluginComponent } from 'quasar';
import Sortable from 'sortablejs';
import { ref } from 'vue';
import { useStore } from 'vuex';
import BaseDialog from '@/components/BaseDialog.vue';

const props = defineProps({
  operator: {
    type: Object,
    required: true,
  },
});

defineEmits(useDialogPluginComponent.emitsObject);

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } =
  useDialogPluginComponent();
// This can't be inside the template due to unwrapping
// See: https://github.com/vuejs/composition-api/issues/317#issuecomment-1069145915
const getDialogRef = () => dialogRef;

const store = useStore();
// Should not be a computed, otherwise the order will get messed up due to polling
const operatorJobs = store.state.job.assigned_job_list.find(
  ({ operator }) => operator._key === props.operator._key,
).assigned_jobs;
// The order is crucial, so can't use an object for reliability reasons
const jobsByWorkOrder = ref([]);
operatorJobs.forEach((job) => {
  let workOrder = jobsByWorkOrder.value.find(
    ({ workOrderKey }) => workOrderKey === job.wo_key,
  );
  if (!workOrder) {
    workOrder = { workOrderKey: job.wo_key, jobs: [] };
    jobsByWorkOrder.value.push(workOrder);
  }
  workOrder.jobs.push({
    ...job,
    wo_sequence: store.state.workorder.wo_map[job.wo_key].sequence,
  });
});

let sortable;
// Using @show and @hide instead of onMounted and onUnmounted because the instance is bound to q-dialog
function onShow() {
  sortable = new Sortable(document.querySelector('.draggable-table table'), {
    ...store.state.drag_options,
    draggable: '.draggable',
    // using the draggable indexes as there is also the thead element in the draggable container
    onEnd: ({ oldDraggableIndex, newDraggableIndex }) => {
      const [removed] = jobsByWorkOrder.value.splice(oldDraggableIndex, 1);
      jobsByWorkOrder.value.splice(newDraggableIndex, 0, removed);
    },
  });
}
function onHide() {
  sortable?.destroy();
}

function save() {
  const newOrder = jobsByWorkOrder.value.flatMap(({ jobs }) =>
    jobs.map(({ _key }) => _key),
  );
  onDialogOK(newOrder);
}

function jobIcon(job) {
  // Set start_from as beginning of day in case there's an hour set
  return new Date(job.start_from).setHours(0, 0, 0) > Date.now()
    ? { name: 'mdi-calendar-clock', color: 'grey-backdrop' }
    : job.next_batch_available
      ? { name: 'mdi-check-circle', color: 'theme-blue' }
      : { name: 'mdi-cube-off', color: 'orange-backdrop' };
}
</script>

<style lang="scss" scoped>
// We are using multiple tbody elements and still want the separators as usual
.draggable-table :deep(tbody tr:last-child td) {
  border-bottom-width: 1px;
}

.draggable-table :deep(td) {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.reorder-dialog-card {
  min-width: 800px;
  max-width: 1200px;
}
</style>

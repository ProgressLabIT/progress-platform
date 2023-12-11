<template>
  <div class="fit column">
    <q-list class="transparent medium text-left q-pa-md" align="left">
      <q-item
        clickable
        v-for="(p, index) in phase_data"
        :key="p.phase_key"
        :name="index"
        class="full-width text-left"
      >
        <!-- PHASE INDEX -->
        <q-item-section avatar class="col-auto">
          <q-avatar
            size="20px"
            :color="p.phase_key == job.phase_key ? 'theme-blue' : 'theme-grey'"
            class="display smaller"
            :class="{ highlight: p.phase_key == job.phase_key }"
          >
            {{ index + 1 }}
          </q-avatar>
        </q-item-section>

        <!-- PHASE ALIAS -->
        <q-item-section>
          <q-item-label
            class="display ellipsis"
            :class="
              p.phase_key == job.phase_key
                ? 'highlight'
                : 'text-low weight-medium'
            "
          >
            {{ p.phase_alias }}
          </q-item-label>
        </q-item-section>

        <!-- PHASE PROGRESS -->
        <q-item-section>
          <div class="row items-center">
            <div class="col">
              <BaseProgressBar :data="p" />
            </div>
            <div class="col-1" />
            <div class="col-auto">
              {{ p.qt_released }} / {{ wo_data.qt_planned }}
            </div>
          </div>
        </q-item-section>

        <!-- PHASE PEOPLE -->
        <q-item-section>
          <div class="row q-gutter-sm justify-end">
            <BaseUserAvatar
              v-for="o in p.assignments.filter((o) => o)"
              :key="o._key"
              :user="o"
              :show_name="false"
            />
          </div>
        </q-item-section>
      </q-item>
    </q-list>
  </div>
</template>

<script>
import LoadingSignal from '@/components/LoadingSignal.vue';
import NoDataAlert from '@/components/NoDataAlert.vue';
import BaseProgressBar from '@/components/BaseProgressBar.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';

export default {
  name: 'WorkSessionProcess',

  components: {
    LoadingSignal,
    NoDataAlert,
    BaseProgressBar,
    BaseUserAvatar,
  },

  props: {
    job: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      vuex_ready: false,
      polling_instance: null,
    };
  },

  computed: {
    wo_data() {
      return this.$store.state.workorder.wo_data || { phase_sequence: [] };
    },

    phase_data() {
      return this.wo_data.phase_sequence.map((phase_key) => {
        const jobs = this.wo_data.jobs
          .filter((job) => job.phase_key === phase_key)
          .sort((a, b) => (a._key > b._key ? -1 : a._key < b._key ? 1 : 0));
        const phase_alias = jobs[0].phase_alias;
        const total_released = jobs.reduce(
          (sum, job) => sum + job.qt_released,
          0,
        );
        const total_progress = Math.floor(
          jobs.reduce((sum, job) => sum + job.progress * job.qt_planned, 0) /
            this.wo_data.qt_planned,
        );
        const critical = jobs.some((job) => job.critical);
        const active = jobs.some((job) => job.active);
        const assignments = jobs.map((job) => job.assigned_to);

        return {
          phase_key,
          phase_alias,
          active,
          critical,
          assignments,
          qt_released: total_released,
          progress: total_progress,
        };
      });
    },
  },
};
</script>

<style lang="css" scoped></style>

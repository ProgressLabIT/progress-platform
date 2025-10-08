import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

export function useTask() {

  const { t } = useI18n();

  const taskStatusOptions = {
    pending: { label: t('pending'), value: 'pending', color: 'transparent', icon: 'mdi-clock-outline' },
    open: { label: t('open'), value: 'open', color: 'theme-blue', icon: 'mdi-circle-outline' },
    completed: { label: t('completed'), value: 'completed', color: 'theme-green', icon: 'mdi-check-circle' },
    canceled: { label: t('canceled'), value: 'canceled', color: 'theme-grey', icon: 'mdi-close-circle' }
  };

  const taskColumns = computed(() => [
    {
      name: 'type',
      field: 'type',
      sortable: true,
      label: t('type').toUpperCase(),
      align: 'left',
    },
    {
      name: 'code',
      field: 'code',
      sortable: true,
      label: t('code').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'title',
      field: 'title',
      sortable: true,
      label: t('title').toUpperCase(),
      align: 'left',
      style: 'max-width: 20vw',
    },
    {
      name: 'status',
      field: 'status',
      sortable: true,
      label: t('status').toUpperCase(),
      align: 'left',
    },
    {
      name: 'assigned_to',
      field: 'assigned_to',
      sortable: false,
      label: t('assigned_to').toUpperCase(),
      align: 'left',
    },
    {
      name: 'start_from',
      field: 'start_from',
      sortable: true,
      align: 'right',
      label: t('start_from').toUpperCase(),
      style: 'max-width: 10vw',
    },
    {
      name: 'due_by',
      field: 'due_by',
      sortable: true,
      align: 'right',
      label: t('due_by').toUpperCase(),
      style: 'max-width: 10vw',
    },
    // {
    //   name: 'created',
    //   field: 'created',
    //   sortable: true,
    //   align: 'right',
    //   label: t('created_date').toUpperCase(),
    //   style: 'max-width: 10vw',
    // },
    {
      name: 'closed',
      field: 'closed',
      sortable: true,
      align: 'right',
      label: t('closed_date').toUpperCase(),
    },
  ]);

  return {
    taskStatusOptions,
    taskColumns,
  };
}



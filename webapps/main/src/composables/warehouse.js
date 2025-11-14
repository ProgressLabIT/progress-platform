import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { shortDateString } from '../lib/TimeHandling';
import { useQueryModel } from '../lib/queryModelFactory';

export function usePositionColumns() {
  const { t } = useI18n();

  return [
    {
      name: '_key',
      field: '_key',
      sortable: true,
      label: 'ID',
      align: 'left',
      style: 'max-width: 10vw',
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
      name: 'owned',
      field: 'owned',
      sortable: true,
      label: t('owned').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'available',
      field: 'available',
      sortable: true,
      label: t('available').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'fixed',
      field: 'fixed',
      sortable: true,
      label: t('fixed').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'disposable',
      field: 'disposable',
      sortable: true,
      label: t('disposable').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'created',
      field: 'created',
      sortable: true,
      align: 'right',
      label: t('creation_date').toUpperCase(),
      style: 'max-width: 5vw',
      format: (val) => (val ? shortDateString(val) : '-'),
    },
  ];
}

export function useMovementColumns() {
  const { t } = useI18n();

  return [
    {
      name: '_key',
      field: '_key',
      sortable: true,
      label: 'ID',
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'movement_list_code',
      field: 'movement_list_code',
      sortable: true,
      label: t('list').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'type',
      field: 'type',
      sortable: true,
      label: t('type').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'status',
      field: 'status',
      sortable: true,
      label: t('status').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'product_code',
      field: 'product_code',
      sortable: true,
      label: t('product.label').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'serial_code',
      field: 'serial_code',
      sortable: true,
      label: t('serial').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw'
    },
    {
      name: 'position_from_code',
      field: 'position_from_code',
      sortable: true,
      label: t('from').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'position_to_code',
      field: 'position_to_code',
      sortable: true,
      label: t('to').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'quantity',
      sortable: true,
      label: t('quantity.long').toUpperCase(),
      align: 'right',
      style: 'max-width: 10vw',
    },
    {
      name: 'created',
      field: 'created',
      sortable: true,
      align: 'right',
      label: t('creation_date').toUpperCase(),
      style: 'max-width: 5vw',
      format: (val) => (val ? shortDateString(val) : '-'),
    },
    {
      name: 'start',
      field: 'start',
      sortable: true,
      align: 'right',
      label: t('start_short').toUpperCase(),
      style: 'max-width: 5vw',
      format: (val) => (val ? shortDateString(val) : '-'),
    },
    {
      name: 'end',
      field: 'end',
      sortable: true,
      align: 'right',
      label: t('end').toUpperCase(),
      style: 'max-width: 5vw',
      format: (val) => (val ? shortDateString(val) : '-'),
    },
    {
      name: 'user',
      field: 'user_key',
      sortable: true,
      label: t('user.label').toUpperCase(),
    }
  ];
}


export function useMovementListColumns() {
  const { t } = useI18n();

  return [
    {
      name: 'id',
      field: '_key',
      sortable: true,
      label: 'ID',
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'code',
      field: 'code',
      sortable: true,
      label: t('code').toUpperCase(),
      align: 'left',
      style: 'max-width: 20vw',
    },
    {
      name: 'type',
      field: 'type',
      sortable: true,
      label: t('type').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'status',
      field: 'status',
      sortable: true,
      label: t('status').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'created',
      field: 'created',
      sortable: true,
      align: 'right',
      label: t('creation_date').toUpperCase(),
      style: 'max-width: 5vw',
      format: (val) => (val ? shortDateString(val) : '-'),
    },
    {
      name: 'start',
      field: 'start',
      sortable: true,
      align: 'right',
      label: t('start').toUpperCase(),
      style: 'max-width: 5vw',
      format: (val) => (val ? shortDateString(val) : '-'),
    },
    {
      name: 'due_by',
      field: 'due_by',
      sortable: true,
      align: 'right',
      label: t('due_by').toUpperCase(),
      style: 'max-width: 5vw',
      format: (val) => (val ? shortDateString(val) : '-'),
    },
    {
      name: 'end',
      field: 'end',
      sortable: true,
      align: 'right',
      label: t('end').toUpperCase(),
      style: 'max-width: 5vw',
      format: (val) => (val ? shortDateString(val) : '-'),
    },
  ]
}


export function useInventoryColumns() {
  const { t } = useI18n();

  return [

    {
      name: 'product_code',
      field: 'product_code',
      sortable: true,
      label: t('warehouse.inventory.product_code').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'product_description',
      field: 'product_description',
      sortable: true,
      label: t('description').toUpperCase(),
      align: 'left',
      style: 'max-width: 40vw',
    },
    {
      name: 'position',
      field: 'path',
      sortable: true,
      label: t('warehouse.inventory.position').toUpperCase(),
      align: 'left',
      style: 'max-width: 40vw',
    },
    {
      name: 'quantity',
      field: 'quantity',
      sortable: true,
      label: t('warehouse.inventory.quantity').toUpperCase(),
      align: 'right',
      style: 'max-width: 10vw',
    },
    {
      name: 'serial',
      field: 'serial_code',
      sortable: true,
      label: t('warehouse.inventory.serial').toUpperCase(),
      align: 'right',
      style: 'max-width: 10vw',
    },

    // {
    //   name: 'owned',
    //   field: 'owned',
    //   sortable: true,
    //   label: t('warehouse.inventory.owned').toUpperCase(),
    //   align: 'left',
    //   style: 'max-width: 10vw',
    // },
    // {
    //   name: 'date_received',
    //   field: 'date_received',
    //   sortable: true,
    //   align: 'right',
    //   label: t('warehouse.inventory.date_received').toUpperCase(),
    //   style: 'max-width: 5vw',
    //   format: (val) => (val ? shortDateString(val) : '-'),
    // },

    // {
    //   name: 'expiration_date',
    //   field: 'expiration_date',
    //   sortable: true,
    //   align: 'right',
    //   label: t('warehouse.inventory.expiration_date').toUpperCase(),
    //   style: 'max-width: 5vw',
    //   format: (val) => (val ? shortDateString(val) : '-'),
    // },
  ];
}

export function useInventoryFilters() {
  const productSearch = ref(useQueryModel(String, 'product_search', null));
  const serialSearch = ref(useQueryModel(String, 'serial_search', null));
  const positionSearch = ref(useQueryModel(String, 'position_search', null));
  const rootPositionKey = ref(useQueryModel(String, 'root_position_key', null));

  const filters = computed({
    get: () => ({
      product_search: productSearch.value,
      position_search: positionSearch.value,
      serial_search: serialSearch.value,
      root_position_key: rootPositionKey.value,
    }),
  });

  const filters_active = computed({
    get: () => {
      return [productSearch, serialSearch, positionSearch, rootPositionKey].filter(({value}) => {
        return !!value;
      }).length;
    },
  });

  return {
    filters,
    productSearch,
    positionSearch,
    serialSearch,
    rootPositionKey,
    filters_active,
  };
}

export function useCountSessionColumns() {
  const { t } = useI18n();

  return [
    {
      name: '_key',
      field: '_key',
      sortable: true,
      label: 'ID',
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'code',
      field: 'code',
      sortable: true,
      label: t('code').toUpperCase(),
      align: 'left',
      style: 'max-width: 15vw',
    },
    {
      name: 'description',
      field: 'description',
      sortable: true,
      label: t('description').toUpperCase(),
      align: 'left',
      style: 'max-width: 25vw',
    },
    {
      name: 'type',
      field: 'type',
      sortable: true,
      label: t('type').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'status',
      field: 'status',
      sortable: true,
      label: t('status').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'coverage_percentage',
      field: 'coverage_percentage',
      sortable: true,
      label: t('warehouse.counting.coverage_percentage').toUpperCase(),
      align: 'right',
      style: 'max-width: 10vw',
      format: (val) => (val !== null && val !== undefined ? `${val.toFixed(1)}%` : '-'),
    },
    {
      name: 'created',
      field: 'created',
      sortable: true,
      align: 'right',
      label: t('creation_date').toUpperCase(),
      style: 'max-width: 5vw',
      format: (val) => (val ? shortDateString(val) : '-'),
    },
    {
      name: 'started',
      field: 'started',
      sortable: true,
      align: 'right',
      label: t('start').toUpperCase(),
      style: 'max-width: 5vw',
      format: (val) => (val ? shortDateString(val) : '-'),
    },
    {
      name: 'completed',
      field: 'completed',
      sortable: true,
      align: 'right',
      label: t('end').toUpperCase(),
      style: 'max-width: 5vw',
      format: (val) => (val ? shortDateString(val) : '-'),
    },
  ];
}

export function useCountSessionFilters() {
  const search = ref(useQueryModel(String, 'search', null));
  const status = ref(useQueryModel(String, 'status', null));
  const type = ref(useQueryModel(String, 'type', null));

  const filters = computed({
    get: () => ({
      search: search.value,
      status: status.value,
      type: type.value,
    }),
  });

  const filters_active = computed({
    get: () => {
      return [search, status, type].filter((ref) => {
        return !!ref.value;
      }).length;
    },
  });

  return {
    filters,
    search,
    status,
    type,
    filters_active,
  };
}

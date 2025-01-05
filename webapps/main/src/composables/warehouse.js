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
      name: 'due_by',
      field: 'due_by',
      sortable: true,
      align: 'right',
      label: t('due_by').toUpperCase(),
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
      name: 'position_code',
      field: 'position_code',
      sortable: true,
      label: t('warehouse.inventory.position').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'serial',
      field: 'serial_code',
      sortable: true,
      label: t('warehouse.inventory.serial').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'quantity',
      field: 'quantity',
      sortable: true,
      label: t('warehouse.inventory.quantity').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },

    {
      name: 'owned',
      field: 'owned',
      sortable: true,
      label: t('warehouse.inventory.owned').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
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
  const product = ref(useQueryModel(String, 'product', null));
  const position = ref(useQueryModel(String, 'position', null));
  const serial = ref(useQueryModel(String, 'serial', null));

  const filters = computed({
    get: () => ({
      product_key: product.value,
      position_key: position.value,
      serial_keys: serial.value,
    }),
  });

  const filters_active = computed({
    get: () => {
      return Object.entries(filters).filter(([value]) => {
        return !!value;
      }).length;
    },
  });

  return {
    product,
    position,
    serial,
    filters,
    filters_active,
  };
}

import { useI18n } from 'vue-i18n';

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
      label: t('product_code').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'position_from_code',
      field: 'position_from_code',
      sortable: true,
      label: t('warehouse.movement.position_from_code').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'position_to_code',
      field: 'position_to_code',
      sortable: true,
      label: t('warehouse.movement.position_to_code').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'qt_planned',
      field: 'qt_planned',
      sortable: true,
      label: t('warehouse.movement.qt_planned').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'qt_confirmed',
      field: 'qt_confirmed',
      sortable: true,
      label: t('warehouse.movement.qt_confirmed').toUpperCase(),
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
    },
    {
      name: 'start',
      field: 'start',
      sortable: true,
      align: 'right',
      label: t('start_date').toUpperCase(),
      style: 'max-width: 5vw',
    },
    {
      name: 'end',
      field: 'end',
      sortable: true,
      align: 'right',
      label: t('end_date').toUpperCase(),
      style: 'max-width: 5vw',
    },
  ];
}

export function useInventoryColumns() {
  const { t } = useI18n();

  return [
    {
      name: 'position_code',
      field: 'position_code',
      sortable: true,
      label: t('warehouse.inventory.position').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },

    {
      name: 'product_code',
      field: 'product_code',
      sortable: true,
      label: t('warehouse.inventory.product_code').toUpperCase(),
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
    {
      name: 'date_received',
      field: 'date_received',
      sortable: true,
      align: 'right',
      label: t('warehouse.inventory.date_received').toUpperCase(),
      style: 'max-width: 5vw',
    },

    {
      name: 'expiration_date',
      field: 'expiration_date',
      sortable: true,
      align: 'right',
      label: t('warehouse.inventory.expiration_date').toUpperCase(),
      style: 'max-width: 5vw',
    },
  ];
}

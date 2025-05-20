import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { capitalizeAll } from '@/boot/filters';
import { shortDateString } from '../lib/TimeHandling';

export function useSerialColumns() {
  const { t } = useI18n();
  const store = useStore();

  function getValueFromField(fieldValue) {
    if (!fieldValue) {
      return '---';
    } else if (fieldValue instanceof Object) {
      return fieldValue.value;
    }
    return fieldValue;
  }

  function customFieldValue(row, key) {
    let returnValue = '---';
    if (row && row['grid_data']) {
      row['grid_data'].forEach((field) => {
        if (field._key === key) {
          returnValue = getValueFromField(field.value);
        }
      });
    }
    return returnValue;
  }

  function getCustomCols() {
    if (!store.state.serial.serial_fields) {
      return [];
    }
    return store.state.serial.serial_fields.map((field) => ({
      name: field.name,
      field: field._key,
      sortable: false,
      align: 'right',
      label: field.name.toUpperCase(),
      style: 'max-width: 5vw',
      custom: true,
      format: (val, row) =>
        capitalizeAll(customFieldValue(row, field._key) || '-'),
    }));
  }

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
      label: t('serial').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    },
    {
      name: 'product_code',
      field: (row) => row?.product?.code,
      sortable: true,
      align: 'left',
      label: t('product.label').toUpperCase(),
      style: 'max-width: 10vw',
      format: (val, row) => capitalizeAll(row?.product?.code || '-'),
    },
    {
      name: 'wo_code',
      field: 'wo_code',
      sortable: true,
      align: 'left',
      label: t('work_order.long').toUpperCase(),
      style: 'max-width: 10vw',
    },
    {
      name: 'project_code',
      field: 'project_code',
      sortable: true,
      align: 'left',
      label: t('project').toUpperCase(),
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
      name: 'released',
      field: 'released',
      sortable: true,
      align: 'right',
      label: t('release_date').toUpperCase(),
      style: 'max-width: 5vw',
      format: (val) => (val ? shortDateString(val) : '-'),
    },
    // {
    //   name: 'available',
    //   field: 'available',
    //   sortable: true,
    //   align: 'right',
    //   label: t('available').toUpperCase()
    // }
  ].concat(getCustomCols());
}

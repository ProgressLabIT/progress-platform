import { Dialog, Notify, exportFile } from 'quasar';
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import PrintDialog from '@/components/PrintDialog.vue';
import { usePrintTemplates } from '@/composables/print-template';

export function usePrintDialog({ context: contextType, contextData }) {
  const { t } = useI18n();
  const store = useStore();

  const context = TemplateContextFactory.create(
    contextType,
    contextData,
    store,
  );

  const { templates, isLoading } = usePrintTemplates({
    context: context.type,
    contextKey: context.getKey(),
  });
  const isAvailable = computed(
    () => !isLoading.value && templates.value.length > 0,
  );

  async function open() {
    return Dialog.create({
      component: PrintDialog,
      componentProps: {
        context,
        templates: templates.value,
      },
    }).onOk(({ src, printTemplate }) => {
      Notify.create({
        message: t('printDialog.downloadWillBegin'),
        type: 'positive',
      });
      exportFile(`${printTemplate.name}.pdf`, src);
    });
  }

  return {
    open,
    isAvailable,
  };
}

const extractDate = (datetime) =>
  datetime ? new Date(datetime).toLocaleDateString() : '-';
const extractTime = (datetime) =>
  datetime ? new Date(datetime).toLocaleTimeString() : '-';

class TemplateContextFactory {
  static create(type, data, store = useStore()) {
    switch (type) {
      case 'issue_type':
        return new IssueTypeContext(data, store);
      case 'step':
        return new BatchContext(data, store);
      case 'serial':
        return new SerialContext(data, store);
      case 'print_template':
        return new PrintTemplateContext(data, store);
      default:
        throw new Error(`Unknown template context type: ${type}`);
    }
  }
}

export class TemplateContext {
  type = 'NONE';
  serial = null;
  product = null;
  workOrder = null;

  /** @protected */
  _store;

  constructor(store = useStore()) {
    this._store = store;
  }

  getKey() {
    return undefined;
  }

  session_data() {
    return this._store.state.session;
  }

  getUser(userKey) {
    if (userKey) {
      let user = this._store.getters.getUserByKey(userKey.replace('User/', ''));
      if (user) {
        return this.formatUsername(user.surname, user.name);
      }
    }
    return '';
  }

  formatUsername(surname, name) {
    let fullName = name;
    if (surname) {
      fullName = fullName + ' ' + surname;
    }
    return fullName;
  }

  getPresetValue(presetName) {
    try {
      switch (presetName) {
        // General presets
        case 'current_date':
          return new Date().toLocaleDateString();
        case 'current_time':
          return new Date().toLocaleTimeString();
        case 'current_user':
          return this.formatUsername(
            this.session_data().user.surname,
            this.session_data().user.name,
          );

        // Serial presets
        case 'serial.code':
          return this.serial?.code;
        case 'serial.qt':
          return this.serial?.quantity;
        case 'serial.create_date':
          return extractDate(this.serial?.created);
        case 'serial.create_time':
          return extractTime(this.serial?.created);
        case 'serial.release_date':
          return extractDate(this.serial?.released);
        case 'serial.release_time':
          return extractTime(this.serial?.released);

        // Product presets
        case 'product.code':
          return this.product?.code;
        case 'product.description':
          return this.product?.description;

        // Job presets
        case 'job.key':
          return this.job?._key;
        case 'job.qt_planned':
          return this.job?.qt_planned;
        case 'job.qt_completed':
          return this.job?.qt_completed;
        case 'job.phase_alias':
          return this.job?.phase_alias;
        case 'job.start_date':
          return extractDate(this.job?.start);
        case 'job.start_time':
          return extractTime(this.job?.start);
        case 'job.end_date':
          return extractDate(this.job?.end);
        case 'job.end_time':
          return extractTime(this.job?.end);

        // Work Order presets
        case 'work_order.code':
          return this.workOrder?.wo_code;
        case 'work_order.qt_planned':
          return this.workOrder?.qt_planned;
        case 'work_order.qt_completed':
          return this.workOrder?.qt_completed;
        case 'work_order.start_date':
          return extractDate(this.workOrder?.start);
        case 'work_order.start_time':
          return extractTime(this.workOrder?.start);
        case 'work_order.end_date':
          return extractDate(this.workOrder?.end);
        case 'work_order.end_time':
          return extractTime(this.workOrder?.end);

        // Project presets
        case 'project.code':
          return this.workOrder?.project_code;

        // Issue presets
        case 'issue.open_date':
          return extractDate(this.issue?.created);
        case 'issue.open_time':
          return extractTime(this.issue?.created);
        case 'issue.open_user':
          return this.getUser(this.issue?.created_by);
        case 'issue.close_date':
          return extractDate(this.issue?.closed);
        case 'issue.close_time':
          return extractTime(this.issue?.closed);
        case 'issue.close_user':
          return this.getUser(this.issue?.closed_by);
        case 'issue.status':
          return this.issue?.open ? 'Open' : 'Closed';
        case 'issue.id':
          return this.issue?._key;

        // Didn't find any
        default:
          return undefined;
      }
    } catch (e) {
      return undefined;
    }
  }

  getCustomFieldValue(_customFieldKey) {
    return undefined;
  }

  setSelectedSerial(serial) {
    this.serial = serial;
  }

  setSelectedProduct(product) {
    this.product = product;
  }

  setSelectedWorkOrder(workOrder) {
    this.workOrder = workOrder;
  }

  setSelectedIssue(issue) {
    this.issue = issue;
  }
}

export class IssueTypeContext extends TemplateContext {
  type = 'issue_type';
  issue;

  constructor(issue, store = useStore()) {
    super(store);
    this.issue = issue;

    const { product, job, work_order: workOrder } = issue.links;
    this.product = product;
    this.job = job;
    this.workOrder = workOrder;
  }

  getKey() {
    return this.issue.issue_type_key;
  }

  getCustomFieldValue(customFieldKey) {
    const customField = this._store.getters.getCustomFieldByKey(customFieldKey);
    const issueType = this._store.getters.getIssueType(
      this.issue.issue_type_key,
    );
    if (!customField || !issueType) {
      return undefined;
    }

    // Only uses the first matching field
    const formField = issueType.form_template.find(
      ({ custom_field_key }) => custom_field_key === customFieldKey,
    );
    if (!formField) {
      return undefined;
    }

    const data = this.issue.data.find(({ _key }) => _key === formField._key);
    return customField.type == 'choice' ? data?.value?.value : data?.value;
  }
}

export class PrintTemplateContext extends TemplateContext {
  type = 'template';
  printTemplate_key;

  constructor(printTemplate_key, store = useStore()) {
    super(store);
    this.printTemplate_key = printTemplate_key;
  }

  getKey() {
    return this.printTemplate_key;
  }
}

export class SerialContext extends TemplateContext {
  type = 'product';
  serial;

  constructor(serial_key, store = useStore()) {
    super(store);
    this.serial = store.getters.getSerialData(serial_key);
  }

  getKey() {
    return this.serial?.product?._key;
  }

  getPresetValue(presetName) {
    try {
      const value = super.getPresetValue(presetName);
      if (value !== undefined) {
        return value;
      }

      switch (presetName) {
        default:
          return undefined;
      }
    } catch (e) {
      return '';
    }
  }

  getCustomFieldValue(customFieldKey) {
    const customField = this._store.getters.getCustomFieldByKey(customFieldKey);

    if (this.serial) {
      const serial_data = this.serial.data.find(
        ({ custom_field_key }) => custom_field_key === customField._key,
      );

      if (serial_data?.value) {
        return customField.type == 'choice'
          ? serial_data.value.value
          : serial_data.value;
      }
    }

    if (this.product?.metadata) {
      const product_metadata_field = this.product.metadata.find(
        ({ custom_field_key }) => custom_field_key === customField._key,
      );
      if (product_metadata_field.value) {
        return customField.type == 'choice'
          ? product_metadata_field?.value?.value
          : product_metadata_field?.value;
      }
    }

    return undefined;
  }
}

export class BatchContext extends TemplateContext {
  type = 'batch';
  batch;
  job;
  serial;
  workOrder;

  constructor(store = useStore()) {
    super(store);
    this.batch = this._store.state.traceability.current_batch_data;
    this.job = this._store.state.traceability.working_job_data;
    this.serial = this.workOrder = this._store.state.workorder.wo_data;
    this.product = (({ product_code, product_description }) => ({
      code: product_code,
      description: product_description,
    }))(this.workOrder);
  }

  getKey() {
    return this.batch._key;
  }

  getCustomFieldValue(customFieldKey) {
    const customField = this._store.getters.getCustomFieldByKey(customFieldKey);

    // Return empty if custom field not found
    if (!customField) {
      return undefined;
    }

    // Check first among serial data, if present
    if (this.batch?.step_data.length) {
      // Only uses the first matching field
      const formField = this.batch.form_fields.find(
        ({ custom_field_key }) => custom_field_key === customFieldKey,
      );

      if (formField) {
        const data = batchStep.form_data.find(
          ({ form_field_key }) => form_field_key === formField._key,
        );
        if (data?.value) {
          return customField.type == 'choice'
            ? data?.value?.value
            : data?.value;
        }
      }
    }

    // If no step data field found or empty, check within serial, if present
    if (this.serial) {
      const serial_data = this.serial.data.find(
        ({ custom_field_key }) => custom_field_key === customField._key,
      );

      if (serial_data?.value) {
        return customField.type == 'choice'
          ? serial_data.value.value
          : serial_data.value;
      }
    }

    // If no batch data field or empty, check within product metadata, if present
    if (this.product?.metadata) {
      const product_metadata_field = this.product.metadata.find(
        ({ custom_field_key }) => custom_field_key === customField._key,
      );
      if (product_metadata_field.value) {
        switch (customField.type) {
          case 'choice':
            return product_metadata_field?.value?.value;
          case 'files':
            return {
              ...product_metadata_field.value,
              path: `/media/product/${this.product._key}/meta/${product_metadata_field.custom_field_key}/${product_metadata_field.value.name}`,
            };
          default:
            return product_metadata_field?.value;
        }
      }
    }

    // Return undefined if no value found
    return undefined;
  }
}

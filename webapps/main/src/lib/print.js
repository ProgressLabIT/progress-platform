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
    contextKey: context.getTemplateContextKey(),
  });
  const isAvailable = computed(
    () => !isLoading.value && templates.value.length > 0,
  );

  async function open() {
    // Start with a clean state
    context.resetState();

    // Open the dialog
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
        return new StepContext(data, store);
      case 'serial':
        return new SerialContext(data, store);
      case 'print_template':
        return new PrintTemplateContext(data, store);
      case 'workorder':
        return new WorkOrderContext(store);
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

  resetState() {
    this.serial = null;
    this.product = null;
    this.workOrder = null;
    this.issue = null;
  }

  getTemplateContextKey() {
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

  getFilePath(fieldInstance, file, fileBucket) {
    const basePath = '/media';
    const bucketMap = {
      product: () =>
        '/product/' +
        [
          this.product._key,
          'meta',
          fieldInstance.custom_field_key,
          file.name,
        ].join('/'),
      step: () =>
        '/traceability/' +
        [
          this.workOrder._key,
          this.batch._key,
          this.step._key,
          fieldInstance.custom_field_key,
          fieldInstance.form_field_key,
          file.name,
        ].join('/'),
      serial: () =>
        '/serial/' +
        [
          this.serial._key,
          fieldInstance.custom_field_key,
          fieldInstance.form_field_key,
          file.name,
        ].join('/'),
      issue: () =>
        '/issue/' + [this.issue._key, fieldInstance._key, file.name].join('/'),
    };
    return basePath + bucketMap[fileBucket]();
  }

  getFieldValueByType(type, fieldInstance, fileBucket) {
    switch (type) {
      case 'choice':
        return fieldInstance?.value?.value;
      case 'files':
        // Use embedded path if present
        return fieldInstance?.value?.length
          ? (fieldInstance?.value?.[0]?.path ??
              this.getFilePath(
                fieldInstance,
                fieldInstance?.value?.[0],
                fileBucket,
              ))
          : undefined;
      default:
        return fieldInstance?.value;
    }
  }

  getPresetValue(presetName) {
    if (presetName?.includes('extra')) {
      return this.getExtraValue(presetName);
    }
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
        case 'job.notes':
          return this.job?.notes;

        // Work Order presets
        case 'work_order.code':
          return this.workOrder?.wo_code;
        case 'work_order.qt_planned':
          return this.workOrder?.qt_planned;
        case 'work_order.qt_completed':
          return this.workOrder?.qt_completed;
        case 'work_order.notes':
          return this.workOrder?.notes;
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

  getExtraValue(presetName) {
    /**
     * Gets a value from a nested object path specified by a preset name string.
     * The preset name is expected to be in dot notation format (e.g. 'serial.extra.one.two').
     * The first part specifies the base object (serial, job, work_order, product, issue)
     * and subsequent parts specify the nested property path to traverse.
     * @param {string} presetName - Dot-notation path to the desired value
     * @returns {*} The value at the specified path, or undefined if path is invalid
     */
    const parts = presetName?.split('.').map(String);
    const base = parts[0];
    const propertyPath = parts?.slice(1); // Everything after the base (e.g., ['extra', 'one', 'two', 'three'])

    const baseObjectMap = {
      serial: this.serial,
      job: this.job,
      work_order: this.workOrder,
      product: this.product,
      issue: this.issue
    };

    if (baseObjectMap[base]) {
      const baseObject = baseObjectMap[base];
      return this.getNestedValue(baseObject, propertyPath);
    }
    return undefined;
  }

  getNestedValue(obj, path) {
    /**
     * Recursively traverses an object to get a nested value based on a path array
     * @param {Object} obj - The object to traverse
     * @param {Array} path - Array of keys representing the path to the desired value
     * @returns {*} The value at the specified path, or undefined if path is invalid
     */
    if (!obj || !path.length) {
      return obj;
    }

    let current = obj;
    for (const key of path ?? []) {
      if (current == null || typeof current !== 'object') {
        return undefined;
      }
      current = current[key];
    }

    return current;
  }

  searchValueInContexts(valueContexts, customField) {
    /**
     * valueContexts is an array of arrays [context, contextValues]
     * that carries data from different contexts order by priority of search,
     * e.g. first current batch data, then serial, then product metadata.
     *
     * If no matching custom field is found in any of the contexts,
     * or the value is falsy or an empty array, it will return an empty string
     * that will be rendered as empty field or no image
     */
    const nothingFound = '';
    for (const [context, contextValues] of valueContexts) {
      if (contextValues?.length) {
        // Only uses the first matching field
        const formField = contextValues.find(
          ({ custom_field_key }) => custom_field_key === customField._key,
        );

        if (formField?.value?.length) {
          return this.getFieldValueByType(customField.type, formField, context);
        }
      }
    }
    return nothingFound;
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

  getTemplateContextKey() {
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

    const valueContexts = [['issue', this.issue?.data]];

    return this.searchValueInContexts(valueContexts, customField);
  }
}

export class PrintTemplateContext extends TemplateContext {
  type = 'template';
  printTemplate_key;

  constructor(printTemplate_key, store = useStore()) {
    super(store);
    this.printTemplate_key = printTemplate_key;
  }

  getTemplateContextKey() {
    return this.printTemplate_key;
  }
}

export class SerialContext extends TemplateContext {
  type = 'product'; // Fetch product templates
  product;
  serial;

  constructor(serial_key, store = useStore()) {
    super(store);
    this.serial = store.getters.getSerialData(serial_key);
    this.product = this.serial?.product;
  }

  getTemplateContextKey() {
    return this.serial?.product?._key;
  }

  getCustomFieldValue(customFieldKey) {
    const customField = this._store.getters.getCustomFieldByKey(customFieldKey);
    if (!customField) {
      return undefined;
    }

    const valueContexts = [
      ['serial', this.serial?.data],
      ['product', this.product?.metadata],
    ];
    return this.searchValueInContexts(valueContexts, customField);
  }
}


export class WorkOrderContext extends TemplateContext {
  type = 'product'; // Fetch product templates

  constructor(store = useStore()) {
    super(store)
    this.workOrder = store.state.workorder.wo_data
    this.serialSource = { work_order_key: this.workOrder?._key }
  }

  getTemplateContextKey() {
    return this.workOrder.product_key
  }

  getCustomFieldValue(customFieldKey) {
    const customField = this._store.getters.getCustomFieldByKey(customFieldKey);
    // Return empty if custom field not found
    if (!customField) {
      return undefined;
    }

    const valueContexts = [
      ['product', this.product?.metadata],
    ];

    // Returns a value if found. If not, will return undefined
    return this.searchValueInContexts(valueContexts, customField);
  }

}

export class StepContext extends TemplateContext {
  type = 'step';
  batch;
  job;
  serial;
  workOrder;

  constructor(step, store = useStore()) {
    super(store);
    this.step = step;
    this.batch = store.state.traceability.current_batch_data;
    this.job = store.state.traceability.working_job_data;
    this.workOrder = store.state.workorder.wo_data;
    this.serialSource = { batch_key: this.batch._key }
  }

  getTemplateContextKey() {
    return this.step._key;
  }

  getCustomFieldValue(customFieldKey) {
    const customField = this._store.getters.getCustomFieldByKey(customFieldKey);
    // Return empty if custom field not found
    if (!customField) {
      return undefined;
    }

    const batch_form_data =
      this._store.state.traceability.current_batch_data.step_data
        .map((s) => s.form_data)
        .flat();

    const valueContexts = [
      ['step', batch_form_data],
      ['serial', this.serial?.data],
      ['product', this.product?.metadata],
    ];

    // Returns a value if found. If not, will return undefined
    return this.searchValueInContexts(valueContexts, customField);
  }
}

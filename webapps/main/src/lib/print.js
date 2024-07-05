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

const extractDate = (datetime) => datetime ? new Date(datetime).toLocaleDateString() : '-';
const extractTime = (datetime) => datetime ? new Date(datetime).toLocaleTimeString() : '-';

class TemplateContextFactory {
  static create(type, data, store = useStore()) {
    switch (type) {
      case 'issue_type':
        return new IssueTypeContext(data, store);
      case 'step':
        return new StepContext(data, store);
      default:
        throw new Error(`Unknown template context type: ${type}`);
    }
  }
}

export class TemplateContext {
  type = 'NONE';
  serial = null;

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
    let fullName = name
    if (surname) {
      fullName = fullName + ' ' + surname
    }
    return fullName
  }

  getPresetValue(presetName) {
    try {
      switch (presetName) {
        case 'current_date':
          return new Date().toLocaleDateString();
        case 'current_time':
          return new Date().toLocaleTimeString();
        case 'current_user':
          return this.formatUsername(
            this.session_data().user.surname,
            this.session_data().user.name,
          );
        case 'serial':
          return this.serial?.code;
        case 'serial_qt':
          return this.serial?.quantity;
        case 'serial_create_date':
          return extractDate(this.serial?.created);
        case 'serial_create_time':
          return extractTime(this.serial?.created);

        default:
          return undefined;
      }
    } catch (e) {
      return '';
    }
  }

  getCustomFieldValue(_customFieldKey) {
    return undefined;
  }

  setSelectedSerial(serial) {
    this.serial = serial;
  }
}

export class IssueTypeContext extends TemplateContext {
  type = 'issue_type';
  issue;

  constructor(issue, store = useStore()) {
    super(store);
    this.issue = issue;
  }

  getKey() {
    return this.issue.issue_type_key;
  }

  getPresetValue(presetName) {
    try {
      const value = super.getPresetValue(presetName);
      if (value !== undefined) {
        return value;
      }

      const { issue } = this;
      const { product, job, work_order: workOrder } = issue.links;

      switch (presetName) {
        case 'issue.open_date':
          return extractDate(issue.created);
        case 'issue.open_time':
          return extractTime(issue.created);
        case 'issue.open_user':
          return this.getUser(issue.created_by);
        case 'issue.close_date':
          return extractDate(issue.closed);
        case 'issue.close_time':
          return extractTime(issue.closed);
        case 'issue.close_user':
          return this.getUser(issue.closed_by);
        case 'issue.status':
          return issue.open ? 'Open' : 'Closed';

        case 'job.key':
          return job._key;
        case 'job.qt_planned':
          return job.qt_planned;
        case 'job.qt_completed':
          return job.qt_completed;
        case 'job.phase_alias':
          return job.phase_alias;
        case 'job.start_date':
          return extractDate(job.start);
        case 'job.start_time':
          return extractTime(job.start);
        case 'job.end_date':
          return extractDate(job.end);
        case 'job.end_time':
          return extractTime(job.end);

        case 'project.code':
          return job.project_code;

        case 'work_order.code':
          return job.wo_code;
        case 'work_order.qt_planned':
          return workOrder.qt_planned;
        case 'work_order.qt_completed':
          return workOrder.qt_completed;
        case 'work_order.start_date':
          return extractDate(workOrder.start);
        case 'work_order.start_time':
          return extractTime(workOrder.start);
        case 'work_order.end_date':
          return extractDate(workOrder.end);
        case 'work_order.end_time':
          return extractTime(workOrder.end);

        case 'product.code':
          return product.code;
        case 'product.description':
          return product.description;

        case 'serial.serial_number':
          if (this.serial) {
            return this.serial.code;
          } else {
            return '';
          }

        default:
          return undefined;
      }
    } catch (e) {
      return '';
    }
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

    const data = this.issue.data.find(
      ({ form_field_key }) => form_field_key === formField._key,
    );
    return data?.value;
  }
}

export class StepContext extends TemplateContext {
  type = 'step';
  step;

  constructor(step, store = useStore()) {
    super(store);
    this.step = step;
  }

  getKey() {
    return this.step._key;
  }

  getPresetValue(presetName) {
    try {
      const value = super.getPresetValue(presetName);
      if (value !== undefined) {
        return value;
      }

      const job = this._store.state.traceability.working_job_data;
      // const batch = this._store.state.traceability.current_batch_data;
      const wo = this._store.state.workorder.wo_data;

      switch (presetName) {
        case 'job.key':
          return job._key;
        case 'job.qt_planned':
          return job.qt_planned;
        case 'job.qt_completed':
          return job.qt_completed;
        case 'job.phase_alias':
          return job.phase_alias;
        case 'job.start_date':
          return extractDate(job.start);
        case 'job.start_time':
          return extractTime(job.start);
        case 'job.end_date':
          return extractDate(job.end);
        case 'job.end_time':
          return extractTime(job.end);

        case 'project.code':
          return wo.project_code;

        case 'work_order.code':
          return wo.wo_code;
        case 'work_order.qt_planned':
          return wo.qt_planned;
        case 'work_order.qt_completed':
          return wo.qt_completed;
        case 'work_order.start_date':
          return extractDate(wo.start);
        case 'work_order.start_time':
          return extractTime(wo.start);
        case 'work_order.end_date':
          return extractDate(wo.end);
        case 'work_order.end_time':
          return extractTime(wo.end);

        case 'product.code':
          return job.product_code;
        case 'product.description':
          return job.product_description;

        default:
          return undefined;
      }
    } catch (e) {
      return '';
    }
  }

  getCustomFieldValue(customFieldKey) {
    const customField = this._store.getters.getCustomFieldByKey(customFieldKey);
    const batchStep = this._store.getters.getBatchStep(this.step._key);
    if (!customField || !batchStep) {
      return undefined;
    }

    // Only uses the first matching field
    const formField = this.step.form_fields.find(
      ({ custom_field_key }) => custom_field_key === customFieldKey,
    );
    if (!formField) {
      return undefined;
    }

    const data = batchStep.form_data.find(
      ({ form_field_key }) => form_field_key === formField._key,
    );
    if (data?.value) {
      return data?.value;
    }

    if (this.serial) {
      const serial_data = this.serial.data.find(
        ({ form_field_key }) => form_field_key === formField._key,
      );

      return serial_data?.value;
    }
  }
}

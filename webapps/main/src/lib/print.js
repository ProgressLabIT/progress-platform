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

const extractDate = (datetime) => new Date(datetime).toLocaleDateString();
const extractTime = (datetime) => new Date(datetime).toLocaleTimeString();

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

  /** @protected */
  _store;

  constructor(store = useStore()) {
    this._store = store;
  }

  getKey() {
    return undefined;
  }

  getPresetValue(presetName) {
    switch (presetName) {
      case 'current_date':
        return new Date().toLocaleDateString();
      case 'current_time':
        return new Date().toLocaleTimeString();
      case 'current_user':
        return this._store.state.auth.user.name;
      default:
        return undefined;
    }
  }

  getCustomFieldValue(_customFieldKey) {
    return undefined;
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
    const value = super.getPresetValue(presetName);
    if (value !== undefined) {
      return value;
    }

    const { issue } = this;
    const { product, job, work_order: workOrder } = issue.links;

    switch (presetName) {
      case 'issue.open_date':
        return extractDate(issue.open_date);
      case 'issue.open_time':
        return extractTime(issue.open_date);
      case 'issue.open_user':
        return issue.open_user;
      case 'issue.close_date':
        return extractDate(issue.close_date);
      case 'issue.close_time':
        return extractTime(issue.close_date);
      case 'issue.close_user':
        return issue.close_user;
      case 'issue.status':
        return issue.status;

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

      default:
        return undefined;
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
    const value = super.getPresetValue(presetName);
    if (value !== undefined) {
      return value;
    }

    const job = this._store.state.traceability.working_job_data;
    const batch = this._store.state.traceability.current_batch_data;

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
        return job.project_code;

      case 'work_order.code':
        return job.wo_code;
      case 'work_order.qt_planned':
        return batch.qt_planned;
      case 'work_order.qt_completed':
        return batch.qt_completed;
      case 'work_order.start_date':
        return extractDate(batch.start);
      case 'work_order.start_time':
        return extractTime(batch.start);
      case 'work_order.end_date':
        return extractDate(batch.end);
      case 'work_order.end_time':
        return extractTime(batch.end);

      case 'product.code':
        return job.product_code;
      case 'product.description':
        return job.product_description;

      default:
        return undefined;
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
    return data?.value;
  }
}

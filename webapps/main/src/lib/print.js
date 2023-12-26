import { Dialog, Notify, exportFile } from 'quasar';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import PrintDialog from '@/components/PrintDialog.vue';

export function usePrintDialog({ context, contextData }) {
  const { t } = useI18n();
  const store = useStore();

  function open() {
    return Dialog.create({
      component: PrintDialog,
      componentProps: {
        context: TemplateContextFactory.create(context, contextData, store),
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

    switch (presetName) {
      case 'issue_open_date':
        return extractDate(this.issue.open_date);
      case 'issue_open_time':
        return extractTime(this.issue.open_date);
      case 'issue_open_user':
        return this.issue.open_user;
      case 'issue_close_date':
        return extractDate(this.issue.close_date);
      case 'issue_close_time':
        return extractTime(this.issue.close_date);
      case 'issue_close_user':
        return this.issue.close_user;
      case 'issue_status':
        return this.issue.status;

      /*
          TODO: Should we get the model data that is linked to the issue? (e.g. product, batch, etc.)
          The issue can be linked to multiple models, so we can:
          - use the first connection
          - ask the user to pick one
          - and/or try to pick it from the UI context (e.g. if the user opened the issue from the work session page, use the related product, job, batch, etc.)
        */
      default:
        return undefined;
    }
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

    const job = this.store.state.traceability.working_job_data;
    const batch = this.store.state.traceability.current_batch_data;

    switch (presetName) {
      case 'job_key':
        return job._key;
      case 'job_qt_planned':
        return job.qt_planned;
      case 'job_qt_completed':
        return job.qt_completed;
      case 'job_phase_alias':
        return job.phase_alias;
      case 'job_start_date':
        return extractDate(job.start);
      case 'job_start_time':
        return extractTime(job.start);
      case 'job_end_date':
        return extractDate(job.end);
      case 'job_end_time':
        return extractTime(job.end);

      case 'project_code':
        return job.project_code;
      case 'work_order_code':
        return job.wo_code;
      case 'work_order_qt_planned':
        return batch.qt_planned;
      case 'work_order_qt_completed':
        return batch.qt_completed;
      case 'work_order_start_date':
        return extractDate(batch.start);
      case 'work_order_start_time':
        return extractTime(batch.start);
      case 'work_order_end_date':
        return extractDate(batch.end);
      case 'work_order_end_time':
        return extractTime(batch.end);

      case 'product_code':
        return job.product_code;
      case 'product_description':
        return job.product_description;

      default:
        return undefined;
    }
  }
}

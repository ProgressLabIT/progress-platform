import { Dialog, Notify, exportFile } from 'quasar';
import { useI18n } from 'vue-i18n';
import PrintDialog from '@/components/PrintDialog.vue';

export function usePrintDialog({ context, contextData }) {
  const { t } = useI18n();

  function open() {
    return Dialog.create({
      component: PrintDialog,
      componentProps: {
        context,
        contextData,
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

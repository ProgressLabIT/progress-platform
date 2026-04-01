import { boot } from 'quasar/wrappers';
import { setAppRouter } from '@/lib/appRouter';

export default boot(({ router }) => {
  setAppRouter(router);
});

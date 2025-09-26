import { Dialog, Notify } from 'quasar';
import { useI18n } from 'vue-i18n';
import { sendEvent } from '@/composables/event.js';
import { useTaskStore } from '@/stores/task.js';


/**
 * Sets up the task navigation guard for the router
 * @param {Router} router - Vue Router instance
 */
export function useTaskNavigationGuard(router) {
  router.beforeEach(async (to, from, next) => {
    try {
      const entityInfo = extractEntityFromRoute(to);

      if (entityInfo) {
        const shouldContinue = await handleEntityNavigation(entityInfo, to);
        if (!shouldContinue) {
          // User chose to cancel navigation
          return next(false);
        }
      }

      next();
    } catch (error) {
      console.error('Navigation guard error:', error);
      next(); // Continue navigation on error
    }
  });
}

/**
 * Extracts entity information from route meta
 * @param {Route} route - Vue Router route object
 * @returns {Object|null} Entity info or null if not an entity route
 */
export function extractEntityFromRoute(route) {
  const entityMeta = route.meta?.entity;
  if (!entityMeta) {
    return null;
  }

  const key = route.params[entityMeta.keyParam];
  if (!key) {
    return null;
  }

  return {
    type: entityMeta.type,
    key: key,
    param: entityMeta.keyParam,
    routeName: route.name
  };
}

/**
 * Handles navigation to entity routes with task context validation
 * @param {Object} entityInfo - Entity information extracted from route
 * @param {Route} route - Vue Router route object
 * @returns {Boolean} Whether navigation should continue
 */
export async function handleEntityNavigation(entityInfo, _route) {
  const taskStore = useTaskStore();
  const activeTask = taskStore.getActiveTask;

  // No active task - continue normally
  if (!activeTask) {
    return true;
  }

  // Check if this entity is already ignored using store method
  if (taskStore.isEntityIgnored(entityInfo.type, entityInfo.key)) {
    return true;
  }

  // Check if entity is already linked to the active task
  const isLinked = activeTask.links?.some(link =>
    link.type === entityInfo.type && link.key === entityInfo.key
  );

  if (isLinked) {
    // Entity is linked - continue with task context
    return true;
  }

  // Check if this entity type can be linked to the current task type
  const canLink = activeTask.allowed_linked_entities?.some(setting =>
    setting.type === entityInfo.type
  );

  if (!canLink) {
    // Can't link this entity type - continue without task context
    return true;
  }

  // Entity not linked but can be linked - prompt user
  const userChoice = await promptNavigationChoice(entityInfo, activeTask);
  return await handleNavigationChoice(userChoice, entityInfo, activeTask);
}

/**
 * Prompts user for navigation decision
 * @param {Object} entityInfo - Entity information
 * @param {Object} activeTask - Active task object
 * @returns {String} User choice: 'link', 'ignore', 'deactivate', or 'cancel'
 */
async function promptNavigationChoice(entityInfo, activeTask) {
  const { t } = useI18n();

  return new Promise((resolve) => {
    Dialog.create({
      title: t('task_navigation.entity_not_linked_title'),
      message: t('task_navigation.entity_not_linked_message', {
        entityType: entityInfo.type,
        entityKey: entityInfo.key,
        taskTitle: activeTask.title || activeTask.code
      }),
      options: {
        type: 'radio',
        model: 'link',
        items: [
          { label: t('task_navigation.link_and_continue'), value: 'link', color: 'primary' },
          { label: t('task_navigation.continue_without_linking'), value: 'ignore', color: 'grey' },
          { label: t('task_navigation.deactivate_task_and_continue'), value: 'deactivate', color: 'orange' }
        ]
      },
      cancel: {
        label: t('task_navigation.cancel_navigation'),
        color: 'negative',
        flat: true
      },
      ok: {
        label: t('task_navigation.continue'),
        color: 'primary'
      },
      persistent: true
    }).onOk((choice) => {
      resolve(choice);
    }).onCancel(() => {
      resolve('cancel');
    });
  });
}

/**
 * Handles the user's navigation choice
 * @param {String} choice - User choice: 'link', 'ignore', 'deactivate', or 'cancel'
 * @param {Object} entityInfo - Entity information
 * @param {Object} activeTask - Active task object
 * @returns {Boolean} Whether navigation should continue
 */
async function handleNavigationChoice(choice, entityInfo, activeTask) {
  const { t } = useI18n();
  const taskStore = useTaskStore();

  switch (choice) {
    case 'link':
      try {
        await linkEntityToTask(entityInfo, activeTask);
        Notify.create({
          message: t('task_navigation.entity_linked_successfully', {
            entityType: entityInfo.type
          }),
          color: 'theme-green',
          timeout: 2000,
          position: 'top',
        });
        return true;
      } catch (error) {
        console.error('Error linking entity to task:', error);
        Notify.create({
          message: t('task_navigation.failed_to_link_entity'),
          color: 'theme-red',
          timeout: 3000,
          position: 'top',
        });
        return false;
      }

    case 'ignore': {
      // Use store method instead of local Set
      taskStore.addIgnoredEntity(entityInfo.type, entityInfo.key);
      return true;
    }

    case 'deactivate':
      // Use store method instead of direct assignment
      taskStore.deactivateTask();
      Notify.create({
        message: t('task_navigation.task_deactivated'),
        color: 'theme-orange',
        timeout: 2000,
        position: 'top',
      });
      return true;

    case 'cancel':
    default:
      return false;
  }
}

/**
 * Links an entity to the active task
 * @param {Object} entityInfo - Entity information
 * @param {Object} activeTask - Active task object
 */
async function linkEntityToTask(entityInfo, activeTask) {
  await sendEvent({
    event_type: 'TASK_LINKED',
    event_data: {
      task_key: activeTask._key,
      link_type: entityInfo.type,
      link_key: entityInfo.key,
    }
  });

  // Update active task data to include the new link
  const taskStore = useTaskStore();
  if (activeTask._key) {
    const updatedTaskData = await taskStore.getTaskData(activeTask._key);
    // Update the task in the store if it exists
    const taskIndex = taskStore.tasks.findIndex(t => t._key === activeTask._key);
    if (taskIndex !== -1) {
      taskStore.tasks[taskIndex] = updatedTaskData;
    }
  }
}

// Note: clearIgnoredEntities and getIgnoredEntities are now available
// as methods on the task store: taskStore.clearIgnoredEntities() and taskStore.getIgnoredEntities()

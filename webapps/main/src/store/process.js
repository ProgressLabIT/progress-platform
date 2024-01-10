import { cloneDeep as _cloneDeep } from 'lodash';
import { api } from '@/boot/axios.js';

/**
 * @type {import('vuex').Module}
 */
const process = {
  state: {
    saved: [],
    temp: [],
    operations: [],
  },

  mutations: {
    /**
     * Use this mutation to add, remove
     * change sequence of process phases
     */
    UPDATE_PROCESS(state, process) {
      state.temp = process;
    },

    LOAD_SAVED_PROCESS(state, process) {
      state.saved = _cloneDeep(process);
      state.temp = _cloneDeep(process);
    },

    ADD_TEMP_PHASE_TEMPLATE(state, { phase_index, template }) {
      state.temp[phase_index].print_templates.push({ ...template, temp: true });
    },

    DELETE_TEMP_PHASE_TEMPLATE(state, { phase_index, template_index }) {
      let phase = state.temp[phase_index];
      phase.print_templates[template_index].temp
        ? phase.print_templates.splice(template_index, 1)
        : (phase.print_templates[template_index].trash = true);
    },

    DELETE_PHASE(state, phase_index) {
      state.temp.splice(phase_index, 1);
    },

    LOAD_OPERATIONS(state, operations) {
      state.operations = operations;
    },

    CANCEL_PROCESS_CHANGES(state) {
      state.temp = _cloneDeep(state.saved);
    },
  },

  actions: {
    async getOperations({ commit }) {
      const { data: operations } = await api.get('operation');

      operations.forEach((operation) => {
        operation.default_phase_steps?.forEach((step) => {
          step.media =
            step.media?.map((media) => ({
              _key: media._key,
              filename: media.name,
              src: `/media/${media._key}`,
              temp: false,
              trash: false,
            })) ?? [];
        });
      });

      commit('LOAD_OPERATIONS', operations);
    },

    async createOperation({ dispatch }, new_operation_data) {
      const { data } = await api.post('operation', new_operation_data);
      await dispatch('getOperations');
      return data.detail._key;
    },

    async updateOperation({ dispatch }, { key, update }) {
      const newMediaByStepIndex = new Map();
      // TODO: use Promise.allSettled and offer retry or abandon for failed requests
      await Promise.all(
        update.default_phase_steps?.flatMap((step, stepIndex) =>
          step.media.map(async (media) => {
            if (!media.temp) {
              return;
            }

            const formData = new FormData();
            formData.append('file', media.data);
            const { data: newMedia } = await api.post('media/create', formData);
            if (!newMediaByStepIndex.has(stepIndex)) {
              newMediaByStepIndex.set(stepIndex, []);
            }
            newMediaByStepIndex.get(stepIndex).push(newMedia.detail._key);
          }),
        ) ?? [],
      );

      await api.patch(`operation/${key}`, {
        ...update,
        default_phase_steps: update.default_phase_steps.map(
          (step, stepIndex) => ({
            ...step,
            media: [
              ...step.media
                .filter(({ trash, temp }) => !trash && !temp)
                .map(({ _key }) => _key),

              ...(newMediaByStepIndex.get(stepIndex) ?? []),
            ],
          }),
        ),
      });

      await dispatch('getOperations');
    },

    async getProcess({ commit }, product_key) {
      async function loadStepMedia(step) {
        const { data } = await api.get(`step/${step._key}/media`);
        step.media = data.map((filename) => ({
          filename,
          src: `/media/step/${step._key}/${filename}`,
          temp: false,
          trash: false,
        }));
      }

      const { data: phases } = await api.get(`product/${product_key}/process`);
      const promises = [];
      phases.forEach((phase) => {
        phase.steps.forEach((step) => {
          if (step.type === 'instruction') {
            promises.push(loadStepMedia(step));
          }
        });
      });
      await Promise.all(promises);
      commit('LOAD_SAVED_PROCESS', phases);
    },

    async saveTempProcess({ dispatch }, data) {
      const { data: updatedProcess } = await api.put(
        `product/${data.product_key}/process`,
        data.new_process,
      );
      // update newly created steps with _key so that the media can be uploaded accordingly
      updatedProcess.forEach((phase, phaseIndex) => {
        phase.steps.forEach((step, stepIndex) => {
          const stepUpdateData = data.new_process[phaseIndex].steps[stepIndex];
          stepUpdateData._key = step._key;
        });
      });

      const newMedia = [];
      const deletedMedia = [];

      const templateUpdates = [];

      data.new_process.forEach((phase) => {
        phase.steps.forEach((step) => {
          if (step.media === undefined) {
            step.media = [];
          }

          step.media.forEach((media) => {
            if (media.trash) {
              deletedMedia.push({
                step_key: step._key,
                filename: media.filename,
              });
            }

            if (media.temp) {
              newMedia.push({
                step_key: step._key,
                media_file: media.data,
              });
            }
          });
        });

        phase.print_templates.forEach((template) => {
          if (template.temp) {
            templateUpdates.push({
              type: 'add',
              context: 'phase',
              context_key: phase._key,
              template_key: template._key,
            });
          }

          if (template.trash) {
            templateUpdates.push({
              type: 'remove',
              context: 'phase',
              context_key: phase._key,
              template_key: template._key,
            });
          }
        });
      });

      const mediaPromises = [];

      deletedMedia.forEach(({ step_key, filename }) => {
        mediaPromises.push(api.delete(`step/${step_key}/media/${filename}`));
      });

      newMedia.forEach(({ step_key, media_file }) => {
        const body = new FormData();
        body.append('media_file', media_file);
        mediaPromises.push(
          api.post(`step/${step_key}/media`, body, {
            headers: { 'Content-Type': 'multipart/form-data' },
          }),
        );
      });

      await Promise.all([
        ...mediaPromises,
        api.post('update-template-assignments', templateUpdates),
      ]);
      await Promise.all([
        dispatch('getProcess', data.product_key),
        dispatch('loadProductDetails', data.product_key),
      ]);
    },
  },
};

export default process;

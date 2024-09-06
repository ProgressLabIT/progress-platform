import { cloneDeep as _cloneDeep } from 'lodash';
import { api } from '@/boot/axios.js';
import { updateListItemByKey as updateProduct } from '@/lib/ListUpdate.js';

const product = {
  state: {
    saved: {},
    temp: {},
    list: [],
    edit_modes: {
      product: false,
      process: false,
      bom: false,
    },
    tags: [],
  },

  mutations: {
    TOGGLE_EDIT_MODE(state, { view, value }) {
      state.edit_modes[view] = value;
    },

    UPDATE_PRODUCT(state, updated_product) {
      updateProduct(state.list, updated_product._key, (product) => {
        for (const field in updated_product) {
          if (field != '_key') {
            product[field] = updated_product[field];
          }
        }
      });
    },

    /**
     * The mutation below is the exact copy of the one above.
     * The duplication is to semantically separate the update
     * of fields that do not need backend sync from those that do
     */
    UPDATE_PRODUCT_NAV_STATE(state, updated_product) {
      updateProduct(state.list, updated_product._key, (product) => {
        for (const field in updated_product) {
          if (field != '_key') {
            product[field] = updated_product[field];
          }
        }
      });
    },

    UPDATE_TEMP_PARAMETER(state, { param, new_value }) {
      state.temp[param] = new_value;
    },

    UPDATE_TEMP_TARGET(state, { param, new_target }) {
      state.temp[param].target = new_target;
    },

    ADD_TEMP_DOC(state, { file, force = false }) {
      const savedFile = state.saved.docs.find(({ name }) => name === file.name);

      // If the file is already saved, and has the same size, the user PROBABLY is trying to restore.
      // They deleted the file, didn't save, and is now trying to re-add it.
      // TODO: Use a better way to check if the file is the same.
      if (savedFile && savedFile.size === file.size && !force) {
        state.temp.docs.push({
          name: file.name,
          size: file.size,
        });
        return;
      }

      state.temp.docs.push({
        name: file.name,
        size: file.size,
        data: file,
        temp: true,
      });
    },

    DELETE_TEMP_DOC(state, doc_index) {
      state.temp.docs.splice(doc_index, 1);
    },

    ADD_TEMP_PRODUCT_TEMPLATE(state, template) {
      state.temp.print_templates.push({ ...template, temp: true });
    },

    DELETE_TEMP_PRODUCT_TEMPLATE(state, template_index) {
      state.temp.print_templates.splice(template_index, 1);
    },

    UPDATE_TEMP_IMAGE(state, new_image) {
      state.temp_files.image = new_image;
    },

    ADD_NEW_PRODUCT(state, new_product_data) {
      state.list.push(new_product_data);
      state.list.sort((a, b) => {
        return a.code > b.code ? 1 : -1;
      });
    },

    LOAD_PRODUCT_LIST(state, product_list) {
      state.list = product_list;
    },

    APPEND_PRODUCT_LIST(state, product_list) {
      if (state.list) {
        for (const product of product_list) {
          state.list.push(product);
        }
      } else {
        state.list = product_list;
      }
    },

    LOAD_PRODUCT_DETAILS(state, product_details) {
      state.saved = _cloneDeep(product_details);
      state.temp = _cloneDeep(product_details);
    },

    CANCEL_PRODUCT_CHANGES(state) {
      state.temp = _cloneDeep(state.saved);
    },

    LOAD_TAGS(state, tag_list) {
      state.tags = tag_list;
    },
  },

  actions: {
    switchActiveState({ commit }, product) {
      api
        .patch(`product/${product._key}`, { active: !product.active })
        .then((resp) => {
          commit('UPDATE_PRODUCT', resp.data.detail);
        });
    },

    moveToTrash({ commit }, product) {
      api.patch('product/' + product._key, { trash: true }).then((resp) => {
        commit('UPDATE_PRODUCT', resp.data.detail);
      });
    },

    restoreProduct({ commit }, product_key) {
      api.patch('product/' + product_key, { trash: false }).then((resp) => {
        commit('UPDATE_PRODUCT', resp.data.detail);
      });
    },

    loadProductList({ commit }, search_params) {
      if (!search_params) {
        search_params = {};
      }
      return new Promise((resolve, reject) => {
        api
          .get('product', { params: search_params })
          .then((resp) => {
            const productList = resp.data;
            productList.forEach((p) => {
              p.last_page = 'home';
              (p.last_phase = 0), (p.last_steps = [0]);
            });
            commit('LOAD_PRODUCT_LIST', productList);
            resolve();
          })
          .catch((err) => {
            window.alert(`Couldn't fetch data from db:\n ${err}`);
            reject();
          });
      });
    },

    appendProductList({ commit }, search_params) {
      if (!search_params) {
        search_params = {};
      }
      return new Promise((resolve, reject) => {
        api
          .get('product', { params: search_params })
          .then((resp) => {
            const productList = resp.data;
            productList.forEach((p) => {
              p.last_page = 'home';
              (p.last_phase = 0), (p.last_steps = [0]);
            });
            commit('APPEND_PRODUCT_LIST', productList);
            resolve();
          })
          .catch((err) => {
            window.alert(`Couldn't fetch data from db:\n ${err}`);
            reject();
          });
      });
    },

    async loadProductDetails({ commit }, product_key) {
      const [
        { data: product },
        { data: print_templates },
        {
          data: { detail: tags },
        },
      ] = await Promise.all([
        api.get(`product/${product_key}`),
        api.get('print-template', {
          params: { context: 'product', context_key: product_key },
        }),
        api.get('tag', {
          params: { context: 'product', context_key: product_key },
        }),
      ]);

      commit('LOAD_PRODUCT_DETAILS', {
        ...product,
        print_templates,
        tags,
      });
    },

    async saveProductChanges(
      context,
      {
        new_product_data,
        new_docs,
        deleted_docs,
        new_templates,
        deleted_templates,
        image,
        tags,
      },
    ) {
      /**
       * this action queues up as many api calls as needed
       * to add/delete product docs and finally to update
       * product parameters. Then returns a promise which resolves
       * only after successfully making all calls and re-fetching
       * updated product data.
       */
      const product_key = new_product_data._key;

      // Initialize requests queue
      const promises = [];

      // For each field, add / delete files
      for (const field of new_product_data?.metadata ?? []) {
        // Check for file fields and return only those that have updates
        const isFileType =
          context.getters.getCustomFieldByKey(field.custom_field_key).type ==
          'files';
        if (isFileType) {
          let to_add = [];
          let to_delete = [];

          field.value?.forEach((file, index, fileslist) => {
            if (file.delete) {
              to_delete.push(file.name);
            } else if (file.temp) {
              to_add.push(file.content);
              // Leave only name and size properties to be saved in the db
              fileslist[index] = { name: file.name, size: file.size };
            }
          });

          const target = {
            bucket: 'product',
            object_key: product_key,
            subfolder: `meta/${field.custom_field_key}`,
          };

          if (to_delete.length) {
            try {
              await api.delete('files', {
                filenames: to_delete,
                ...target,
              });
            } catch (error) {
              console.log(error);
              window.alert(error);
            }
          }

          if (to_add.length) {
            const add_body = new FormData();
            Object.entries(target).forEach(([k, v]) => add_body.append(k, v));
            to_add.forEach((file) => add_body.append('contents', file));
            try {
              await api.post('/files', add_body, {
                headers: {
                  'Content-type': 'multipart/form-data',
                },
              });
            } catch (error) {
              console.log(error);
              window.alert(error);
            }
          }
        }
      }

      // Queue api calls to delete product docs
      if (deleted_docs != null) {
        deleted_docs.forEach((d) => {
          promises.push(api.delete(`product/${product_key}/doc/${d.name}`));
        });
      }

      if (deleted_templates != null || new_templates != null) {
        const template_updates = [
          ...deleted_templates.map((t) => ({
            type: 'remove',
            context: 'product',
            context_key: product_key,
            template_key: t._key,
          })),
          ...new_templates.map((t) => ({
            type: 'add',
            context: 'product',
            context_key: product_key,
            template_key: t._key,
          })),
        ];
        promises.push(
          api.post('update-template-assignments', template_updates),
        );
      }

      // Queue api calls to add product docs
      if (new_docs != null) {
        new_docs.forEach((d) => {
          const body = new FormData();
          body.append('new_doc', d.data);
          promises.push(
            api.post(`product/${product_key}/doc`, body, {
              headers: {
                'Content-type': 'multipart/form-data',
              },
            }),
          );
        });
      }

      // Queue request to delete or update product image
      if (image.delete) {
        promises.push(api.delete(`product/${product_key}/image`));
      }

      if (image.new) {
        const body = new FormData();
        body.append('new_image', image.new);
        promises.push(
          api.put(`product/${product_key}/image`, body, {
            headers: {
              'Content-type': 'multipart/form-data',
            },
          }),
        );
      }

      if (tags.add.length > 0 || tags.remove.length > 0) {
        promises.push(
          api.post('tag/update-connections', [
            ...tags.add.map((tag) => ({
              type: 'add',
              context: 'product',
              context_key: product_key,
              tag_key: tag._key,
            })),
            ...tags.remove.map((tag) => ({
              type: 'remove',
              context: 'product',
              context_key: product_key,
              tag_key: tag._key,
            })),
          ]),
        );
      }

      // Queue request to update product metadata
      promises.push(api.put(`product/${product_key}`, new_product_data));

      return Promise.all(promises);
    },

    loadTags({ commit }) {
      return new Promise((resolve) => {
        api.get('tag').then((resp) => {
          commit('LOAD_TAGS', resp.data.detail);
          resolve();
        });
      });
    },
  },

  getters: {
    productCatalog: (state) => (show_active_only, tag_search) => {
      return state.list.filter((p) => {
        const deleted = p.trash;
        const active_filter = !show_active_only || p.active;
        const tag_filter =
          !tag_search || p.tags.some((t) => t._key === tag_search);
        return !deleted && active_filter && tag_filter;
      });
    },

    productData: (state) => (product_key) => {
      return state.list.find((p) => p._key == product_key);
    },

    tags: (state) => () => {
      return state.tags;
    },
  },
};

export default product;

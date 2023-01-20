import { createStore } from 'vuex'
import { cloneDeep as _cloneDeep } from 'lodash'
import { api, axios } from '@/boot/axios.js'
import { updateListItemByKey as updateProduct } from '@/lib/ListUpdate.js' 

const product = {

  state: {
    saved: {},
    temp: {},
    list: [],
    edit_modes: {
      product: false,
      process: false,
      bom: false
    }
  },

  mutations: {

    TOGGLE_EDIT_MODE(state, { view, value }) {
      state.edit_modes[view] = value
    },

    UPDATE_PRODUCT(state, updated_product) {
      updateProduct(state.list, updated_product._key, product => {
        for (const field in updated_product) {
          if (field != '_key') {
            product[field] = updated_product[field]
          }
        }
      })
    },

    /**
     * The mutation below is the exact copy of the one above. 
     * The duplication is to semantically separate the update
     * of fields that do not need backend sync from those that do
     */
    UPDATE_PRODUCT_NAV_STATE(state, updated_product) {
      updateProduct(state.list, updated_product._key, product => {
        for (const field in updated_product) {
          if (field != '_key') {
            product[field] = updated_product[field]
          }
        }
      })
    },

    UPDATE_TEMP_PARAMETER(state, { param, new_value }) {
      state.temp[param] = new_value
    },

    UPDATE_TEMP_TARGET(state, { param, new_target} ) {
      state.temp[param].target = new_target
    },

    ADD_TEMP_DOC(state, file) {     
      // check if the file is not already saved but temporarily deleted
      const already_saved = state.saved.docs.some( d => d.name == file.name)
      
      // simply restore metadata if the file is already saved
      const file_to_add = {
        name: file.name,
        size: file.size,
      }

      // if not, add file content and temp flag
      if (!already_saved) {
        file_to_add.data = file
        file_to_add.temp = true
      }

      state.temp.docs.push(file_to_add)
    },

    DELETE_TEMP_DOC(state, doc_index) {
      state.temp.docs.splice(doc_index, 1)
    },

    UPDATE_TEMP_IMAGE(state, new_image) {
      state.temp_files.image = new_image
    },

    ADD_NEW_PRODUCT(state, new_product_data) {
      state.list.push(new_product_data)
      state.list.sort( (a,b) => {
        return a.code > b.code ? 1 : -1
      })
    },

    LOAD_PRODUCT_LIST(state, product_list) {
      state.list = product_list
    },

    LOAD_PRODUCT_DETAILS(state, product_details) {
      state.saved = _cloneDeep(product_details)
      state.temp = _cloneDeep(product_details)
    },

    CANCEL_PRODUCT_CHANGES(state) {
      state.temp = _cloneDeep(state.saved)
    }
  },

  actions: {
    switchActiveState({ commit }, product) {
      api.patch(
        `product/${product._key}`,
        { active: !product.active }
      )
      .then( resp => {
        commit('UPDATE_PRODUCT', resp.data.detail )
      })
    },

    moveToTrash({ commit }, product) {
      api.patch(
        'product/' + product._key,
        { trash: true }
      )
      .then( resp => {
        commit('UPDATE_PRODUCT', resp.data.detail )
      }) 
    },

    restoreProduct({ commit }, product_key) {
      api.patch(
        'product/' + product_key,
        { trash: false }
      )
      .then( resp => {
        commit('UPDATE_PRODUCT', resp.data.detail )
      })
    },

    loadProductList({ commit }) {
      return new Promise( (resolve, reject) => {
        api.get('product')
        .then(resp => {
          const productList = resp.data
          productList.forEach( p => {
            p.last_page = 'home'
            p.last_phase = 0,
            p.last_steps = [0]
          })
          commit('LOAD_PRODUCT_LIST', productList)
          resolve()
        })
        .catch(err => {        
          window.alert(`Couldn't fetch data from db:\n ${err}`)
          reject()
        })
      })
    },

    loadProductDetails({ commit }, product_key) {
      api.get(`product/${product_key}`)
        .then( resp => {
          commit('LOAD_PRODUCT_DETAILS', resp.data)
        })
    },


    saveProductChanges(context, {
      new_product_data,
      new_docs,
      deleted_docs,
      image
    }) {

      /**
       * this action queues up as many api calls as needed 
       * to add/delete product docs and finally to update
       * product parameters. Then returns a promise which resolves
       * only after successfully making all calls and re-fetching
       * updated product data.
       */
      const product_key = new_product_data._key
      
      // Initialize requests queue
      const api_calls = []

      // Queue api calls to delete product docs
      if (deleted_docs != null) {
        deleted_docs.forEach( d => {
          api_calls.push(api.delete(`product/${product_key}/doc/${d.name}`))
        })
      }

      // Queue api calls to add product docs
      if (new_docs != null) {
        new_docs.forEach( d => {
          const body = new FormData()
          body.append('new_doc', d.data)
          api_calls.push(
            api.post(`product/${product_key}/doc`, body, {
              headers: {
              'Content-type': 'multipart/form-data'
              }
            })
          )
        })
      }

      // Queue request to delete or update product image
      if (image.delete) {
        api_calls.push(api.delete(`product/${product_key}/image`))
      }

      if (image.new) {
        const body = new FormData()
        body.append('new_image', image.new)
        api_calls.push(
          api.put(`product/${product_key}/image`, body, {
            headers: {
              'Content-type': 'multipart/form-data'
            }
          })
        )
      }

      // Queue request to update product metadata
      api_calls.push(api.put(`product/${product_key}`, new_product_data))

      // Execute requests returning a promise
      return new Promise ( (resolve, reject) => {
        axios.all(api_calls)
        .then(() => {
          resolve()
        })
        .catch(err => reject(err))
      })
    },

  },

  getters: {

    productCatalog: (state) => (show_active_only) => {
      return state.list.filter( p => {
        const deleted = p.trash 
        const active_filter = !show_active_only || p.active
        return !deleted && active_filter
      })
    },

    productData: (state) => (product_key) => {
      return state.list.find( p => p._key == product_key)
    }
  }
}

export default product

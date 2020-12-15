<template>
  <v-container fill-height fluid>
    <v-row class="fill-height mx-0">
      
      <!-- LEFT COLUMN -->
      <v-col cols="4" class="fill-height d-flex flex-column justify-space-between">
        <!-- PRODUCT IMAGE -->
        <v-card outlined>
          <v-hover v-slot="{ hover }">
            <v-img height="30vh"
              :src="img_src" 
              :gradient="product.active ? '' : 'to top right, rgba(100,100,100,.33), rgba(25,25,25,.7)'">

              <v-row 
                class="fill-height" 
                align="center" 
                justify="center">

                <v-btn absolute bottom right
                  v-show="hover && !edit_mode && !no_image"
                  small
                  :color="$theme.grey" 
                  @click.stop="showMedia('img')"
                  class="">
                  <v-icon>search</v-icon>
                </v-btn>

                <v-col cols="auto" v-if="no_image" class="text-center">
                  <v-icon x-large :color="$theme.white_low">
                    mdi-image-off-outline
                  </v-icon>
                  <p class="display smaller mt-2">
                    Nessuna immagine
                  </p>
                </v-col>


                <!-- IMAGE LOADING -->
                <template v-slot:placeholder>
                  <!-- If file exists, show loading indication -->
                  <v-progress-circular indeterminate :color="$theme.gray"></v-progress-circular>
                </template>


                <v-container v-if="edit_mode" 
                  style="position:absolute"
                  class="pa-0 fill d-flex flex-column justify-space-between">
                  <v-sheet class="surface-1 text-center smaller display weight-bold">
                    modifica immagine
                  </v-sheet>

                  <!-- <v-sheet class="surface-1"> -->
                  <v-row align="end" class="ma-2">
                    <v-btn v-if="new_image || new_image_url === 'deleted'"
                      small :color="$theme.orange"
                      @click="clearTempImg">
                      ripristina originale
                    </v-btn>
                    <v-btn v-else-if="!no_image"
                      small
                      :color="$theme.red" 
                      @click="deleteImg">
                      <v-icon>delete</v-icon>
                    </v-btn>
                    <v-spacer></v-spacer>
                    <input 
                      type="file"
                      ref="upload_img"
                      style="display: none"
                      accept="image/*"
                      @change="updateImg($event.target.files[0])"/>
                    <v-btn small
                      :color="$theme.grey" 
                      @click="$refs.upload_img.click()">
                      <v-icon>mdi-upload</v-icon>
                    </v-btn>
                    <v-btn 
                      v-if="img_src != ''"
                      small 
                      :color="$theme.grey" 
                      @click.stop="showMedia('img')"
                      class="ml-2">
                      <v-icon>search</v-icon>
                    </v-btn>
                  </v-row>  
                </v-container>
              </v-row>  
            </v-img>
          </v-hover>
        </v-card>

        <!-- PRODUCT CODE -->
        <div class="mt-6">
          <h4 class="weight-bold medium">CODICE PRODOTTO</h4>
          <h1 v-if="!edit_mode" class="display highlight">{{ product.code }}</h1>
          <v-text-field v-else 
            hide-details
            :value="temp_code"
            @blur="updateField('code', $event.target.value.toUpperCase())"
            class="input-uppercase">
          </v-text-field>
        </div>

        <!-- PRODUCT DESCRIPTION -->
        <div class="mt-6">
          <h4 class="weight-bold medium">DESCRIZIONE</h4>
          <h3 v-if="!edit_mode" class="highlight weight-bold mt-1">{{ product.description }}</h3> 
          <v-textarea v-else 
            hide-details
            :value="temp_desc"
            @blur="updateField('description', $event.target.value)">
          </v-textarea>  
        </div>
        

        <!-- PRODUCT TAGS -->
<!--         <h4 class="weight-bold medium">TAG</h4>
        <v-row justify="start" class="mx-0 pt-2">            
          <v-chip small
            v-for="tag in product.tags" 
            :key="tag"
            class="mr-2">
            {{ tag }}
          </v-chip>
        </v-row>           -->

        <v-spacer></v-spacer>

        <v-btn 
          v-if="!edit_mode"
          :color="$theme.blue"
          @click="activateEditMode"
          >
          MODIFICA
        </v-btn>

        <div v-else>
          <v-btn block class="mb-2" :color="$theme.green" @click="saveChanges">
            <div v-if="!saving">
              SALVA
            </div>
            <v-progress-circular v-else indeterminate :color="$theme.white"/>
          </v-btn>
          <v-btn block :color="$theme.grey" :disabled="saving" @click="cancelChanges">ANNULLA</v-btn>
        </div>  

        <!-- CANCEL CONFIRMATION -->
        <v-snackbar
          top :timeout="2000"
          :color="$theme.grey"
          v-model="show_cancel_confirmation">
          Modifiche annullate
          <v-btn text @click.native="show_cancel_confirmation = false">OK</v-btn>
        </v-snackbar>

        <!-- SAVE NOTIFICATION -->
        <v-snackbar
          top :timeout="2000"
          :color="$theme.green"
          v-model="show_save_confirmation">
          Prodotto aggiornato
          <v-btn text :color="$theme.white" @click.native="show_save_confirmation = false">
            <v-icon>close</v-icon>
          </v-btn>
        </v-snackbar>

      </v-col>  
    
      <!-- PRODUCT DATA -->
      <v-col cols="8" class="pl-4 fill-height d-flex flex-column">
          <v-row class="mt-n3 pr-0" align="start">
            
            <!-- PARAMETERS -->
            <v-col cols="6">
              <v-card flat> 
                <ProductParamsCard 
                  :product="product" 
                  :edit_mode="edit_mode">
                </ProductParamsCard>
              </v-card>
            </v-col>  

            <!-- DOCS -->
            <v-col cols="6">
              <v-card flat> 
                <v-container class="px-5 py-4 fill">
                  <h5 class="display medium highlight mb-6">
                    Documenti
                  </h5>
                  <v-hover v-slot:default="{ hover }"
                    v-for="(doc, index) in docs" :key="index">
                    <v-row 
                      no-gutters
                      :style="hover ? `background: var(--hover-bg-blue)` : `` "
                      style="cursor: pointer;"
                      class="body-2 pa-2 mx-n2 flex-nowrap"
                      @click="showMedia(index)">
                      <v-col cols="8">
                        <span  :class="'temp' in doc ? 'font-italic' : ''">
                          {{ doc.name }} {{ 'temp' in doc ? ' (non salvato)' : ''}}
                        </span>
                      </v-col>
                      <v-hover 
                        v-if="edit_mode" 
                        v-slot:default="{ hover: closeHover }">
                        <v-col  @click.stop="deleteDoc(index)" cols="auto">
                          <v-icon small class="ml-2"
                            v-show="hover"
                            :style="closeHover ? `color: ${$theme.red}` : ''"
                            >close</v-icon>
                        </v-col>
                      </v-hover>
                      <v-spacer></v-spacer>
                      <v-col cols="auto" class="text-right">
                        {{ doc.size | bytes }}
                      </v-col>
                    </v-row >
                  </v-hover>
                  <v-row v-if="edit_mode" class="mt-4">                    
                    <input multiple 
                      type="file"
                      ref="upload_doc"
                      style="display: none"
                      accept="application/pdf, image/*"
                      @change="addFiles($event.target.files)"/>
                    <v-hover v-slot:default="{ hover }">
                        <v-btn text block class="pl-6 medium"
                          :color="hover ? $theme.blue : $theme.white_low"
                          @click="$refs.upload_doc.click()">
                          <v-row justify="space-between" align="center">
                            aggiungi documento
                            <v-icon>attach_file</v-icon>
                          </v-row>
                        </v-btn>
                    </v-hover>
                  </v-row>
                </v-container>
              </v-card>
            </v-col>  
          </v-row> 

          <v-lazy>
            <MediaViewer 
              :show="show_media >= 0 || show_media === 'img' " 
              @close="show_media = -1" 
              v-bind="{ media_name, media_src}">
              <template v-slot:context-title>
               PRODUCT CODE: {{ product.code }}
              </template>
            </MediaViewer>
          </v-lazy>

          <v-spacer></v-spacer>

          <!-- PRODUCT ACTIONS -->
          <v-row class="mt-auto flex-grow-0">
            <v-spacer></v-spacer>
            <v-col cols="auto" class="pb-0">
              <v-btn :color="$theme.blue">Crea ordine</v-btn>
            </v-col>  
          
            <v-col cols="auto"  class="pb-0">
              <v-btn :color="$theme.red">Elimina</v-btn>
            </v-col>  
          </v-row>  
      </v-col>

    </v-row>  
  </v-container>
</template>

<script>
import ProductParamsCard from '@/components/ProductParamsCard.vue'
import { mapState, mapActions } from 'vuex'
import MediaViewer from '@/components/MediaViewer.vue'

export default {

  name: 'ProductHome',
  
  components: {
    ProductParamsCard,
    MediaViewer
  },

  data() {
    return {
      saving: false,
      show_cancel_confirmation: false,
      show_save_confirmation: false,
      show_media: -1,
      new_files: null,
      new_image: null,
      new_image_url: '',
      no_image: false
      // zoom: 100
    };
  },

  computed: {

    product_key() {
      return this.$route.params.product_key
    },

    ...mapState({
      product: state => state.product.temp
    }),

    edit_mode: {
      get() {
        return this.$store.state.product.edit_modes.product
      },
      set(value) {
        this.$store.commit('TOGGLE_EDIT_MODE', { view: 'product', value })
      }
    },

    saved_img_path() {
      return `/media/product/${this.product_key}/image.jpg`
    },

    img_src() {
      return this.new_image_url ? this.new_image_url : this.saved_img_path
    },

    temp_code() {
      return this.product.code
    },

    temp_desc() {
      return this.product.description
    },

    docs() {
      return this.product.docs
    },

    saved_docs() {
      return this.$store.state.product.saved.docs
    },

    media_name() {
      if (this.show_media == -1) { return '' }
      else if (this.show_media === 'img') { return 'Product image'}
      else { return this.docs[this.show_media].name }
    },

    media_src() {
      
      if (this.show_media === 'img') {
        return this.img_src
      }

      else if (this.show_media >= 0) {
        const doc = this.docs[this.show_media]
        let path = ''

        if (doc.temp) {
          path = window.URL.createObjectURL(doc.data)
        }
        else path = `/media/product/${this.product_key}/doc/${encodeURI(this.media_name)}`

        return path
      }

      else return null
    },

  },

  methods: {
    ...mapActions(['loadProductDetails']),

    // deltaPcString(p) {
    //   let pc_sign = p.delta_pc > 0 ? '+' : ''
    //   return '('.concat(pc_sign, p.delta_pc, '%)')
    // },

    activateEditMode() {
      this.temp_code = this.product.code
      this.temp_desc = this.product.description

      this.edit_mode = true
    },

    updateImg(img) {
      // let url = this.new_image_url
      // if (url) window.URL.revokeObjectURL(url)
      this.new_image_url = window.URL.createObjectURL(img)
      this.new_image = img
      this.no_image = false
    },

    clearTempImg() {
      window.URL.revokeObjectURL(this.new_image_url)
      this.new_image_url = null
      this.new_image = null
      this.no_image = false
    },

    deleteImg() {
      // this is a fake URL to make v-img show placeholder
      this.new_image_url = 'deleted'
    },

    updateField(field, value) {
      this.$store.commit('UPDATE_TEMP_PARAMETER', { 
        param: field, 
        new_value: value 
      })
    },

    addFiles(file_list) {
      const files = Array.from(file_list)
      // Don't add files already in the list
      files.forEach( (f, i) => {
        const already_in_list = this.docs.some( d => f.name == d.name )
        if (already_in_list) {
          const replace = window.confirm(`Esiste già un documento con nome “${f.name}", vuoi sostituirlo?`)
          if (replace) { this.$store.commit('DELETE_TEMP_DOC', i) }
          else { return }
        }
        this.$store.commit('ADD_TEMP_DOC', f)
      }) 
    },

    deleteDoc(index) {
      this.$store.commit('DELETE_TEMP_DOC', index)
    },

    showMedia(value) {
        this.show_media = value
    },

    saveChanges() {
      this.saving = true
      const old_doc_list = this.$store.state.product.saved.docs
      const new_doc_list = this.product.docs
      let product_update = {
        new_product_data: this.product,
        deleted_docs: old_doc_list.filter( 
          o => !new_doc_list.some( n => n.name === o.name)
        ),
        image: {
          new: this.new_image,
          delete: this.new_image_url === 'deleted'
        }
      }

      if (this.new_docs){
        product_update.new_docs = new_doc_list.filter( d => 'temp' in d )
      }

      this.$store.dispatch('saveProductChanges', product_update)
        .then(async () => {
        // Show progress long enough the let user notice something is going on
        // even if the update is instantaneous
          // setTimeout(() => {
            await this.$store.dispatch('loadProductDetails', this.product_key)
            this.show_save_confirmation = true
            this.edit_mode = false
            this.clearTempImg()
            this.saving = false
          // }, 1500)
        })
        .catch(err => {
          window.alert(err)
        })
    },

    cancelChanges() {
      this.$store.commit('CANCEL_PRODUCT_CHANGES')
      this.show_cancel_confirmation = true
      this.edit_mode = false
    },

  },

  watch: {
    img_src() {
      let test = new XMLHttpRequest()
      test.open('HEAD', this.img_src, false)
      test.send()
      if (test.status === 404) {
        this.no_image = true
      }
    }
  }
};
</script>

<style lang="css" scoped>
</style>

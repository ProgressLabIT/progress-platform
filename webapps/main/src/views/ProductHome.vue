<template>
  <v-container fill-height fluid>
    <v-row class="fill-height mx-0">
      
      <!-- LEFT COLUMN -->
      <v-col cols="4" class="fill-height d-flex flex-column justify-space-between">
        <!-- PRODUCT IMAGE -->
        <v-card outlined>
          <v-img height="30vh"
            :src="img_src" 
            :style="product.active ? '' : 'filter:grayscale(1) brightness(.5)'">
          </v-img>
        </v-card>

        <!-- PRODUCT CODE -->
        <div class="mt-6">
          <h4 class="weight-bold medium">CODICE PRODOTTO</h4>
          <h1 v-if="!edit_mode" class="display highlight">{{ product.code }}</h1>
          <v-text-field v-else 
            hide-details
            :value="temp_code"
            @keyup="this.code = this.code.toUpperCase()"
            @blur="updateField('code', $event.target.value)"
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
          ATTIVA MODIFICHE
        </v-btn>

        <div v-else>
          <v-btn block class="mb-2" :color="$theme.green" @click="saveChanges">
            <div v-if="!saving">
              SALVA
            </div>
            <v-progress-circular v-else indeterminate :color="$theme.white"/>
          </v-btn>
          <v-btn block :color="$theme.grey" @click="cancelChanges">ANNULLA</v-btn>
        </div>  
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

            <!-- #PERFORMANCE -->
            <!-- <v-col cols="6">
              <v-card flat height="35vh"> 
                <v-container class="px-5 py-4">                  
                  <v-row justify="space-between" no-gutters>
                    <v-col cols="auto">
                    
                    <h4 class="display medium highlight mb-4">performance</h4>
                    </v-col>
                    <v-spacer></v-spacer>
                    <v-col cols="auto">
                    
                      <span class="medium">Media 12m | Var. Obiettivo</span> -->
                    <!-- <v-icon>arrow_drop_down</v-icon> -->
                  <!--   </v-col>
                  </v-row>
                  <v-row v-for="(p, key) in perf_list" :key="key" >
                    <v-col cols="2">
                      <span class="text-uppercase smaller weight-bold">
                        {{ p.name }}
                      </span>
                    </v-col>

                    <v-spacer></v-spacer>

                    <v-col cols="4">
                      <span v-if="!key.includes('cost')">
                        {{ p.average | duration }}
                      </span>
                      <span v-else>
                        {{ p.average }}
                      </span>
                    </v-col>
                    <v-spacer></v-spacer>
                    <v-col cols="5" >
                      <span v-if="!key.includes('cost')">
                       {{ p.delta_abs > 0 ? '+' : ''}}{{ p.delta_abs | duration }} {{ deltaPcString(p) }}
                      </span>   
                      <span v-else>
                        {{ p.delta_abs > 0 ? '+' : ''}}{{ p.delta_abs }} EUR {{ deltaPcString(p) }}
                      </span>
                    </v-col> -->
                 <!--  </v-row>

                </v-container>
              </v-card>
            </v-col>  
 -->
            <!-- KPIs 
            <v-col cols="6">
              <v-card flat height="35vh"> 
                <v-container class="px-5 py-4">                  
                  <h4 class="display medium highlight">ordini</h4>
                </v-container>
              </v-card>
            </v-col>  

            ISSUES
            <v-col cols="6">
              <v-card flat height="35vh"> 
                <v-container class="px-5 py-4">                  
                  <h4 class="display medium highlight">segnalazioni</h4>
                </v-container>
              </v-card>
            </v-col> -->  
          </v-row> 

          <v-spacer></v-spacer>
          <!-- PRODUCT ACTIONS -->
          <v-row class="mt-auto flex-grow-0">
            <v-spacer></v-spacer>
            <v-col cols="auto" class="pb-0">
              <v-btn :color="$theme.blue">Crea ordine</v-btn>
            </v-col>  
            <v-col cols="auto"  class="pb-0">
              <v-btn :color="$theme.blue">Crea segnalazione</v-btn>
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
// import {api} from '@/lib/apiCall.js'
import ProductParamsCard from '@/components/ProductParamsCard.vue'
import { mapState, mapActions } from 'vuex'

export default {

  name: 'ProductHome',
  
  components: {
    ProductParamsCard
  },

  data() {
    return {
      saving: false,
      edit_mode: false,
    };
  },

  computed: {

    product_key() {
      return this.$route.params.item_key
    },

    img_src() {
      return `/pics/products/${this.product_key}.jpeg`
    },
    
    ...mapState({
      product: state => state.product.temp
    }),

    temp_code() {
      return this.product.code
    },

    temp_desc() {
      return this.product.description
    }

  },

  methods: {
    ...mapActions(['loadProductDetails']),

    deltaPcString(p) {
      let pc_sign = p.delta_pc > 0 ? '+' : ''
      return '('.concat(pc_sign, p.delta_pc, '%)')
    },

    activateEditMode() {
      this.temp_code = this.product.code
      this.temp_desc = this.product.description

      this.edit_mode = true
    },

    updateField(field, value) {
      this.$store.commit('UPDATE_TEMP_PARAMETER', { 
        param: field, 
        new_value: value 
      })
    },

    saveChanges() {
      this.saving = true
      let product_update = {
        product_key: this.product_key,
        updated_product: this.product
      }
      this.$store.dispatch('saveProductChanges', product_update)
        // .then(() => {
        // Show progress long enough the let user notice something is going on
        // even if the update is instantaneous
          setTimeout(() => {
            this.saving = false
            this.edit_mode = false
          }, 1500)
        // }).catch(err => {
        //   window.alert(err)
        //   this.saving = false
        //   this.edit_mode = false
        // })
    },

    cancelChanges() {
      this.$store.commit('CANCEL_PRODUCT_CHANGES')
      this.edit_mode = false
    }
  },

  created() {
    this.loadProductDetails(this.product_key)
  },

};
</script>

<style lang="css" scoped>
</style>

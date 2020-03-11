<template>
  <div>
    <h5 class="mb-2">MEDIA</h5>
    <v-row class="ml-n1">
      <v-col class="pa-1" cols="3" v-for="(media, index) in media_list" :key="index">
        <v-hover v-slot:default="{ hover }">
          <v-card outlined>
            <v-img 
              :src="media.src" 
              aspect-ratio="1.7778">
              
              <v-sheet color="rgba(100,100,100,.8)">
                <v-row v-if="media.temp" align="start" justify="center" class="mx-1">
                  <span class="smaller text-uppercase weight-bold">Non salvato</span>
                </v-row>
              </v-sheet>
              
              <v-sheet 
                v-if="media.trash"
                color="rgba(231, 29, 54, .8)">
                <v-row align="start" justify="center" class="mx-1">
                  <span class="smaller text-uppercase weight-bold">Eliminato</span>
                </v-row>
              </v-sheet>
          <!--     <v-overlay absolute v-if="media.trash"
                :color="$theme.black"
                class="crossed">
              </v-overlay> -->
              <v-overlay v-show="hover" :color="$theme.grey" absolute>
                <v-row 
                  v-show="hover"
                  class="fill-height" 
                  align="center" 
                  justify="space-between">

                  <!-- SHOW MEDIA SCREEN -->
                  <v-btn 
                    fab x-small 
                    :color="$theme.grey" 
                    @click.stop="showMedia(media)">
                    <v-icon>search</v-icon>
                  </v-btn>

                  <!-- DELETE MEDIA -->
                  <v-btn 
                    v-if="edit_mode && !media.trash"
                    fab x-small 
                    :color="$theme.red" 
                    @click.stop="deleteMedia(index)">
                    <v-icon>delete</v-icon>
                  </v-btn>

                  <!-- RESTORE MEDIA -->
                  <v-btn 
                    v-if="edit_mode && media.trash"
                    fab x-small 
                    :color="$theme.orange" 
                    @click.stop="restoreMedia(index)">
                    <v-icon>restore_from_trash</v-icon>
                  </v-btn>

                </v-row>
              </v-overlay>
            </v-img>
          </v-card>
        </v-hover>
      </v-col>  
      <v-hover v-slot:default="{ hover: hover2 }">
        <v-col 
          v-if="edit_mode" 
          cols="3" 
          class="align-self-center text-center"
          @click="$refs.upload.click()"
          style="cursor: pointer;">
          <input 
            type="file" multiple
            ref="upload"
            style="display: none"
            accept="image/*"
            @change="addMedia($event.target.files)"/>
          <v-icon :color="hover2 ? $theme.whitehigh : $theme.whitelow">add_a_photo</v-icon>              
          <p class="smaller text-uppercase mt-2">Aggiungi media</p>
        </v-col>  
      </v-hover>
    </v-row>  

    <v-lazy>
      <MediaViewer
        :show="show_media_screen"
        :media_name="selected_media.filename"
        :media_src="selected_media.src"
        type="img"
        @close="show_media_screen=false">
      </MediaViewer>
    </v-lazy>

  </div>
</template>

<script>
import MediaViewer from '@/components/MediaViewer.vue'

export default {

  name: 'StepInstruction',

  props: ['phase_no', 'step_no', 'edit_mode'],

  components: {
    MediaViewer
  },

  data() {
    return {
      // media_list: [],
      selected_media: {},
      show_media_screen: false
    }
  },

  computed: {

    pic_no() {
      const rand = Math.random()*5
      return Math.ceil(rand)
    },

    step_data() {
      return this.$store.state.process.temp[this.phase_no].steps[this.step_no]
    },

    media_list() {
      return this.step_data.media
    },

    step_key() {
      return this.step_data._id.split("/")[1]
    },
  },

  methods: {

    showMedia(media) {
      this.selected_media = media
      this.show_media_screen = true
    },

    addMedia(file_list) {
      const media = Array.from(file_list)
      media.forEach( m => {
        const temp_src = window.URL.createObjectURL(m)
        this.$store.commit("ADD_TEMP_MEDIA", { 
          phase_no: this.phase_no,
          step_no: this.step_no,
          media: {
            filename: m.name,
            src: temp_src,
            data: m,
            temp: true,
            trash: false
          }
        })
      })     
    },

    deleteMedia(index) {
      const media_to_delete = this.media_list[index]
      if (media_to_delete.temp) {
        this.$store.commit('DELETE_TEMP_MEDIA', {
          phase_no: this.phase_no,
          step_no: this.step_no,
          index: index
        })
      } 
      else {
        this.$store.commit('DELETE_SAVED_MEDIA', {
          phase_no: this.phase_no,
          step_no: this.step_no,
          index: index
        })
      }
    },

    restoreMedia(index) {
      this.$store.commit('RESTORE_SAVED_MEDIA', {
        phase_no: this.phase_no,
        step_no: this.step_no,
        index: index
      })
    },  
  },

};
</script>

<style lang="css" scoped>
</style>

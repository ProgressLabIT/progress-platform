<template>
  <div>
    <h5 class="mb-2 text-uppercase">
      {{ $tc('phase.instruction_title') }}
    </h5>
    <v-row class="ml-n1">
      <v-col class="pa-1" cols="3" v-for="(media, index) in media_list" :key="index">
        <v-hover v-slot:default="{ hover }">
          <v-card outlined>
            <v-img 
              :src="media.src" 
              aspect-ratio="1.7778">

              <template v-slot:placeholder>
                <v-row v-if="media.filename.endsWith('.pdf')"
                  align="center" justify="center" class="fill-height">
                  <v-icon x-large :color="$theme.white_low">mdi-file-document-outline</v-icon>
                </v-row>

                <v-row v-else align="center" justify="center" class="fill-height">
                  <v-progress-circular indeterminate></v-progress-circular>
                </v-row>
              </template>
              
              <v-sheet color="rgba(100,100,100,.8)">
                <v-row v-if="media.temp" align="start" justify="center" class="mx-1">
                  <span class="smaller text-uppercase weight-bold">
                    {{ $tc('phase.media_not_saved') | capitalize }}
                  </span>
                </v-row>
              </v-sheet>
              
              <v-sheet 
                v-if="media.trash"
                color="rgba(231, 29, 54, .8)">
                <v-row align="start" justify="center" class="mx-1">
                  <span class="smaller text-uppercase weight-bold">
                    {{ $tc('phase.media_deleted') | capitalize }}
                  </span>
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

                  <!-- MEDIA TITLE -->
                  <v-tooltip top>
                    <template v-slot:activator="{on}">
                      <v-btn fab x-small :color="$theme.grey" v-on="on">
                        <v-icon>info</v-icon>
                      </v-btn>
                    </template>
                    <span >
                      {{media.filename}}
                    </span>
                  </v-tooltip>

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
            accept="image/*, application/pdf"
            @change="addMedia($event.target.files)"/>
          <v-icon :color="hover2 ? $theme.white_high : $theme.white_low">add_a_photo</v-icon>              
          <p class="smaller text-uppercase mt-2">
            {{ $tc('phase.add_media') | capitalize }}
          </p>
        </v-col>  
      </v-hover>
    </v-row>  

    <v-lazy>
      <MediaViewer
        :show="show_media_screen"
        :media_name="selected_media.filename"
        :media_src="selected_media.src"
        @close="show_media_screen=false">
      </MediaViewer>
    </v-lazy>

  </div>
</template>

<script>
import MediaViewer from '@/components/MediaViewer.vue'

export default {

  name: 'StepInstruction',

  props: ['phase_index', 'step_index', 'edit_mode'],

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

    pic_index() {
      const rand = Math.random()*5
      return Math.ceil(rand)
    },

    step_data() {
      return this.$store.state.process.temp[this.phase_index].steps[this.step_index]
    },

    media_list() {
      return this.step_data.media
    },

    step_key() {
      return this.step_data._key
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
          phase_index: this.phase_index,
          step_index: this.step_index,
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
          phase_index: this.phase_index,
          step_index: this.step_index,
          index: index
        })
      } 
      else {
        this.$store.commit('DELETE_SAVED_MEDIA', {
          phase_index: this.phase_index,
          step_index: this.step_index,
          index: index
        })
      }
    },

    restoreMedia(index) {
      this.$store.commit('RESTORE_SAVED_MEDIA', {
        phase_index: this.phase_index,
        step_index: this.step_index,
        index: index
      })
    },  
  },

};
</script>

<style lang="css" scoped>
</style>

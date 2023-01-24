<template>
  <div class="text-h5 text-uppercase q-mt-xl">
    {{ $t('phase.instruction_title') }}
  </div>
  <div class="row q-col-gutter-md q-mt-md" id="media-list">
    <div
      v-for="(media, index) in media_list"
      :key="index"
      class="col-3"
      @mouseenter="over_media = index"
      @mouseleave="over_media = null">

      <q-card square bordered>
        <!-- MEDIA TITLE -->
        <q-tooltip class="smaller text-center">
          {{ media.filename }}
        </q-tooltip>

        <q-img
          :src="media.src"
          ratio="1.7778"
          no-native-menu
          no-spinner>
          <template #error>
            <div class="row flex-center">
              <q-icon
                size="xl"
                :name="media.filename.endsWith('.pdf') ? 'mdi-file-document-outline': 'mdi-error'"
                color="text-low">
              </q-icon>
            </div>
          </template>
        </q-img>

        <div
          v-show="media.temp"
          class="absolute-top text-center smaller text-uppercase weight-bold"
          style="background-color: rgba(100, 100, 100, .8);">
          {{ $capitalize($t('unsaved')) }}
        </div>
        <div
          v-show="media.trash"
          class="absolute-top text-center smaller text-uppercase weight-bold"
          style="background-color: rgba(231, 29, 54, .8);">
          {{ $capitalize($t('phase.media_deleted')) }}
        </div>

        <div
          v-show="over_media == index"
          class="absolute-full" style="background-color: #0007;">
          <div class="row fit flex-center">

            <!-- SHOW MEDIA SCREEN -->
            <q-btn
              fab padding="xs"
              color="theme-grey"
              icon="mdi-magnify"
              class="q-mr-sm"
              @click.stop="showMedia(media)">
            </q-btn>

            <template v-if="edit_mode">

              <!-- DELETE MEDIA -->
              <q-btn v-if="!media.trash"
                fab padding="xs"
                color="theme-red"
                icon="mdi-delete"
                @click.stop="deleteMedia(index)">
              </q-btn>

              <!-- RESTORE MEDIA -->
              <q-btn v-else
                fab padding="xs"
                color="theme-orange"
                icon="mdi-upload"
                @click.stop="restoreMedia(index)">
              </q-btn>

            </template>
          </div>
        </div>
      </q-card>
    </div>
  </div>

  <MediaViewer
    :show="show_media_screen"
    :media_name="selected_media.filename"
    :media_src="selected_media.src"
    @close="show_media_screen=false">
  </MediaViewer>

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
      over_media: null,
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

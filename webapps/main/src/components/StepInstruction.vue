<template>
  <div class="text-h5 text-uppercase q-mt-xl">
    {{ $t('phase.instruction_title') }}
  </div>
  <div class="row q-col-gutter-md q-mt-md" id="media-list">
    <div
      v-for="(media, index) in media_list"
      :key="index"
      class="col-3 items-center column"
      :class="{ undraggable: !edit_mode }"
      @mouseenter="over_media = index"
      @mouseleave="over_media = null">

      <q-card square bordered class="full-width">
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
            <div class="row fit flex-center surface1">
              <q-icon
                size="xl"
                :name="media.filename.endsWith('.pdf') ? 'mdi-file-document-outline': 'mdi-error'"
                class="text-low">
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
      <!-- <q-icon
        v-if="edit_mode"
        name="mdi-drag-horizontal-variant"
        size="md"
        class="dragme">
      </q-icon> -->
    </div>
    <div class="col-3">
      <q-btn
        flat
        v-if="edit_mode"
        class="column flex-center q-pt-md q-pb-sm"
        @click="$refs.upload.click()"
        style="cursor: pointer">
        <input
          type="file"
          multiple
          ref="upload"
          style="display: none"
          accept="image/*, application/pdf"
          @change="addMedia($event.target.files)" />
        <q-icon size="md" name="mdi-camera-plus" />
        <div class="q-mt-sm smaller">
          {{ $capitalize($t('phase.add_media')) }}
        </div>
      </q-btn>
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
import Sortable from 'sortablejs'
import MediaViewer from '@/components/MediaViewer.vue'

export default {

  name: 'StepInstruction',

  props: ['phase_index', 'step_index', 'edit_mode'],

  components: {
    MediaViewer
  },

  data() {
    return {
      sortable: undefined,
      over_media: null,
      selected_media: {},
      show_media_screen: false
    }
  },

  computed: {
    step_data() {
      return this.$store.state.process.temp[this.phase_index].steps[this.step_index]
    },

    media_list() {
      return this.step_data ? this.step_data.media : []
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

    /* IMPLEMENT MEDIA SORTING AFTER PROVIDING API */

    // initSortable(selector) {
    //   const _self = this
    //   let container = document.querySelector(selector)
    //   if (container) {
    //     Sortable.create(container, {
    //       ..._self.$store.state.drag_options,
    //       filter: '.undraggable',
    //       handle: '.dragme',
    //       dragClass: 'dragging',
    //       // use onEnd event provided by SortableJs library
    //       onEnd: ({ newIndex, oldIndex }) => {
    //         _self.dragging = false
    //         const moved = _self.media_list.splice(oldIndex, 1)[0]
    //         _self.media_list.splice(newIndex, 0, moved)
    //         _self.updateTabIndex({ oldIndex, newIndex })
    //       }
    //     })
    //   }
    // }
  },

  // mounted() {
  //   this.sortable = this.initSortable('#media-list')
  // },

  // updated() {
  //   this.sortable = this.initSortable('#media-list')
  // }

};
</script>

<style lang="css" scoped>
</style>

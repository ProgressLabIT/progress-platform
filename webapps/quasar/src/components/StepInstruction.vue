<template>
  <div>
    TEST

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

<template>
  <!-- <v-card class="flex-grow-1 scroll" color="transparent"> -->
    <v-container fluid class="pa-0 fill" ref="step_card">

      <v-card class="fill" max-height="100%" >
        <v-toolbar dense >
          <v-row align="center" ref="stepper">
            <v-col cols="auto">
              <h5 class="highlight text-uppercase mr-6">lotto n. {{ 3 }}</h5>
            </v-col>
            <template v-for="(step, index) in procedure">
              <v-col 
                cols="auto" 
                class="px-1"
                :key="step._id">
                <v-avatar 
                  :color="current_step_index == index ? $theme.blue : 'transparent'" 
                  size="20" 
                  class="d-flex text-center smaller font-weight-medium pointer"
                  @click="current_step_index = index">
                  <span :class="current_step_index == index ? 'solid-white weight-bold': ''">{{ index + 1 }}</span>
                </v-avatar>
              </v-col>
              <v-divider 
                v-if="index < procedure.length - 1"
                :key="index">
              </v-divider>
            </template>
            <v-col cols="auto">
              <h5 class="ml-6 highlight text-uppercase">
                passo {{ current_step_index + 1 }} / {{ procedure.length}}
              </h5>
            </v-col>
          </v-row>
        </v-toolbar>
        <v-window 
          continuous
          :show-arrows="false"
          v-model="step_image_index">
          <v-window-item 
            v-for="(img, index) in step_media" 
            :key="index" 
            eager
            class="no-transition">
            <v-img eager :src="displayed_image_src" :height="image_height">


              <template v-slot:placeholder>
                NO IMAGE
              </template>

              <template v-if="step_media.length > 1">
                <v-row no-gutters
                  class="fill mx-0" 
                  style="position:absolute">
                  <v-col cols="6" @click="show('prev')">
                  </v-col>
                  <v-col cols="6" @click="show('next')">
                  </v-col>
                </v-row>
                <v-row class="fill-height" justify="center" align="end">
                  <v-card tile raised
                    v-for="(media, index) in step_media" 
                    :key="index" 
                    height="50px" 
                    width="70px"
                    class="ma-2"
                    :style="step_image_index == index ? 'border-bottom: solid 2px' + $theme.blue : ''"
                    :img="media_base_path + '/' + media"
                    @mouseenter="step_image_index = index">
                  </v-card>
                </v-row>
              </template>
            </v-img>
          </v-window-item>
        </v-window>
      </v-card>
    </v-container>
  <!-- </v-card> -->
</template>

<script>
import { cloneDeep as _cloneDeep } from 'lodash'

export default {

  name: 'WorkSessionSteps',

  props: {
    parameters: {
      type: Object,
      default: () => {
        return { 
          step_check: 'single',
          step_check_force_order: false,
          release_style: 'job',
          production_batch_qt: 1,        
        }
      }
    },
    procedure: {
      type: Array,
      default: () => []
    }
  },

  data () {
    return {
      current_step_index: 0,
      step_image_index: 0,
      media_root_path: '/media/step/',
      runs: [],
      stepper_height: 0,
      image_height: 0,
    }
  },

  computed: {
    current_step() {
      return this.procedure[this.current_step_index]
    },

    step_media() {
      return this.current_step.media
    },

    media_base_path() {
      return this.media_root_path + this.current_step._id.split('/')[1]
    },

    displayed_image_src() {
      return this.media_base_path + '/' + this.step_media[this.step_image_index]
    },
  },

  methods: {
    startRun() {
      this.runs.push(_cloneDeep(this.procedure))
    },

    show(which) {
      console.log('Go to ', which)
      const len = this.step_media.length

      if (which == 'next') {
        this.step_image_index == len - 1 
        ? this.step_image_index = 0 
        : this.step_image_index++
      }

      else if (which == 'prev') {
        this.step_image_index == 0 
        ? this.step_image_index = len - 1 
        : this.step_image_index--
      }
    }
  },

  mounted() {
    const stepper_height = this.$refs.stepper.clientHeight
    const card_height = this.$refs.step_card.clientHeight
    this.image_height = card_height - stepper_height
  },

  watch: {
    current_step_index() {
      this.step_image_index = 0
    }
  }
}
</script>

<style lang="css" scoped>
</style>
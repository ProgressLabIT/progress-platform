<template>
  <v-container class="px-5 py-4 fill" >

    <template v-if="docs.length">
      <v-hover v-slot:default="{ hover }"
        v-for="(doc, index) in docs" :key="index">
        <v-row
          no-gutters
          :style="hover ? `background: var(--hover-bg-blue)` : `` "
          style="cursor: pointer;"
          class="body-1 px-4 py-4 mx-n2 flex-nowrap"
          @click="showMedia(index)">
          <v-col cols="8">
            <span  :class="'temp' in doc ? 'font-italic' : ''">
              {{ doc.name }}
            </span>
          </v-col>

          <v-spacer></v-spacer>

          <v-col cols="auto" class="text-right">
            {{ doc.size | bytes }}
          </v-col>
        </v-row >
      </v-hover>
    </template>

    <NoDataAlert v-else>{{ $tc('document.missing')}}</NoDataAlert>

    <v-lazy>
      <MediaViewer
        :show="show_media >= 0 || show_media === 'img' "
        @close="show_media = -1"
        v-bind="{ media_name, media_src}">
        <template v-slot:context-title>
         {{ $tc('product.code').toUpperCase() }}: {{ product.code }}
        </template>
      </MediaViewer>
    </v-lazy>


  </v-container>
</template>

<script>
import MediaViewer from '@/components/MediaViewer.vue'
import NoDataAlert from '@/components/NoDataAlert.vue'

export default {

  name: 'WorkSessionDocs',

  components: {
    MediaViewer,
    NoDataAlert
  },

  props: {
    job: {
      type: Object,
      required: true
    }
  },

  data () {
    return {
      show_media: -1
    }
  },

  computed: {

    product_key () {
      return this.job.product_key
    },

    docs () {
      return this.job.job_docs || []
    },

    media_name() {
      if (this.show_media == -1) { return '' }
      else if (this.show_media === 'img') { return 'Product image'}
      else { return this.docs[this.show_media].name }
    },

    img_src () {
      return `/media/product/${this.product_key}/image.jpg`
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
    showMedia(value) {
        this.show_media = value
    },
  },
}
</script>

<style lang="css" scoped>
</style>

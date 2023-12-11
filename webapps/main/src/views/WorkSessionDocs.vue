<template>
  <div class="fit column q-px-md q-py-md scroll">
    <template v-if="docs.length">
      <q-list>
        <q-item
          v-for="(doc, index) in docs"
          :key="index"
          clickable
          @click="showMedia(index)"
        >
          <q-item-section :class="'temp' in doc ? 'font-italic' : ''">
            {{ doc.name }}
          </q-item-section>
          <q-item-section side>
            {{ $bytes(doc.size) }}
          </q-item-section>
        </q-item>
      </q-list>
    </template>

    <NoDataAlert v-else>
      {{ $t('document.missing') }}
    </NoDataAlert>

    <MediaViewer
      :show="show_media >= 0 || show_media === 'img'"
      @close="show_media = -1"
      v-bind="{ media_name, media_src }"
    >
      <template v-slot:context-title>
        {{ $t('product.code').toUpperCase() }}: {{ product.code }}
      </template>
    </MediaViewer>
  </div>
</template>

<script>
import MediaViewer from '@/components/MediaViewer.vue';
import NoDataAlert from '@/components/NoDataAlert.vue';

export default {
  name: 'WorkSessionDocs',

  components: {
    MediaViewer,
    NoDataAlert,
  },

  props: {
    job: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      show_media: -1,
    };
  },

  computed: {
    product_key() {
      return this.job.product_key;
    },

    docs() {
      return this.job.job_docs || [];
    },

    media_name() {
      if (this.show_media == -1) {
        return '';
      } else if (this.show_media === 'img') {
        return 'Product image';
      } else {
        return this.docs[this.show_media].name;
      }
    },

    img_src() {
      return `/media/product/${this.product_key}/image.jpg`;
    },

    media_src() {
      if (this.show_media === 'img') {
        return this.img_src;
      } else if (this.show_media >= 0) {
        const doc = this.docs[this.show_media];
        let path = '';

        if (doc.temp) {
          path = window.URL.createObjectURL(doc.data);
        } else
          path = `/media/product/${this.product_key}/doc/${encodeURI(
            this.media_name,
          )}`;

        return path;
      } else return null;
    },
  },

  methods: {
    showMedia(value) {
      this.show_media = value;
    },
  },
};
</script>

<style lang="css" scoped></style>

<template>
  <div
    :style="
      'background-color: ' +
      ($q.dark.isActive ? 'rgba(255, 255, 255, 0.07)' : 'rgba(0, 0, 0, 0.05)')
    "
  >
    <div class="row justify-between items-center q-pl-sm q-py-sm">
      <div class="q-ml-xs text-low">
        {{ label }}
        <span v-if="mandatory" class="text-theme-red"> * </span>
      </div>
      <q-btn
        flat
        padding="xs sm"
        class="q-mr-xs"
        color="low"
        :disable="disable"
        size="md"
        @click="$refs.upload_files.click()"
      >
        <span v-if="!disable" class="smaller q-mr-xs">
          {{ $t('add') }}
        </span>
        <q-icon
          :name="disable ? 'mdi-folder-outline' : 'mdi-folder-plus-outline'"
        />
      </q-btn>
    </div>
    <q-list v-if="files" dense class="q-pb-md">
      <q-item
        v-for="(file, index) in shown_files"
        :key="index"
        clickable
        @click="showMedia(index)"
      >
        <q-item-section
          :class="{
            'text-italic': !disable && file.temp,
            'text-strike': !disable && file.delete,
            'text-disabled': !disable && file.delete,
          }"
        >
          {{ file.name }}
          {{
            !disable && file.temp ? '(' + $capitalize($t('unsaved')) + ')' : ''
          }}
        </q-item-section>
        <q-item-section side class="text-right">
          {{ $bytes(file.size) }}
        </q-item-section>
        <q-item-section v-if="!disable" side>
          <q-btn
            round
            flat
            size="sm"
            style="margin-right: -6px"
            :icon="file.delete ? 'mdi-delete-restore' : 'mdi-close'"
            @click.stop="
              $emit(file.delete ? 'restoreFile' : 'deleteFile', index)
            "
          >
          </q-btn>
        </q-item-section>
      </q-item>
    </q-list>

    <input
      ref="upload_files"
      multiple
      type="file"
      style="display: none"
      accept="*"
      @change="$emit('addFiles', $event.target.files)"
    />

    <MediaViewer
      v-if="show_media >= 0"
      :show="show_media >= 0"
      v-bind="{ media_name, media_src }"
      @close="show_media = -1"
    >
    </MediaViewer>
  </div>
</template>

<script>
import MediaViewer from '@/components/MediaViewer.vue';

export default {
  name: 'FilesList',

  components: {
    MediaViewer,
  },

  props: {
    label: {
      type: String,
      default: 'Files',
    },
    files: {
      type: Array,
      default: () => [],
    },
    disable: {
      type: Boolean,
      default: true,
    },
    rootPath: {
      type: String,
      required: true,
    },
    mandatory: {
      type: Boolean,
      default: false,
    },
  },

  emits: ['addFiles', 'deleteFile', 'restoreFile'],

  data() {
    return {
      show_media: -1,
    };
  },

  computed: {
    shown_files() {
      return this.disable ? this.files.filter((f) => !f.temp) : this.files;
    },

    media_src() {
      return (
        this.files[this.show_media]?.path ||
        this.rootPath + '/' + this.media_name
      );
    },

    media_name() {
      if (this.show_media == -1) {
        return '';
      } else {
        return this.files[this.show_media].name;
      }
    },
  },

  methods: {
    getFileName(path) {
      return path.split('/').pop();
    },

    showMedia(value) {
      this.show_media = value;
    },

    async ensureFileDataAvailable() {
      // Check if temporary files stored in blob URLs are available
      // This can happen if the page is reloaded, when file is not available, but metadata is still there.

      if (!this.files) {
        return;
      }

      for (const [index, file] of this.files.entries()) {
        if (file.temp && file.path?.startsWith('blob:')) {
          try {
            const response = await fetch(file.path);
            if (!response.ok || !(await response.blob())) {
              this.$emit('deleteFile', index);
            }
          } catch (error) {
            console.warn(`File ${file.name} is not accessible:`, error);
            this.$emit('deleteFile', index);
          }
        }
      }
    },
  },

  mounted() {
    this.ensureFileDataAvailable();
  },
};
</script>

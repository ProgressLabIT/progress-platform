<template>
  <!-- TODO: OBJECT STORAGE MIGRATION - Update FilesList for object storage
       1. Replace rootPath-based media_src with object storage URLs
       2. Update ensureFileDataAvailable() for object storage access
       3. Handle signed URL expiration and refresh -->
  <div
    :style="
      'background-color: ' +
      ($q.dark.isActive ? 'rgba(255, 255, 255, 0.07)' : 'rgba(0, 0, 0, 0.05)')
    "
  >
    <div class="row justify-between items-center q-pl-sm" :class="dense ? 'q-py-xs' : 'q-py-sm'">
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
            @click.stop="deleteFile(index)"
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
      @change="addFiles($event.target.files)"
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

<script setup>
import { ref, computed, onMounted } from 'vue';
import MediaViewer from '@/components/MediaViewer.vue';

const props = defineProps({
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
  dense: {
    type: Boolean,
    default: false,
  },
  rootPath: {
    type: String,
    required: true,
  },
  mandatory: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['addFiles', 'deleteFile', 'restoreFile']);

const show_media = ref(-1);
const upload_files = ref(null);

const shown_files = computed(() => {
  return props.disable ? props.files.filter((f) => !f.temp) : props.files;
});

const media_src = computed(() => {
  // TODO: OBJECT STORAGE MIGRATION - Replace path concatenation with object storage URL generation
  return (
    props.files[show_media.value]?.path ||
    props.rootPath + '/' + media_name.value
  );
});

const media_name = computed(() => {
  if (show_media.value == -1) {
    return '';
  } else {
    return props.files[show_media.value].name;
  }
});

const showMedia = (value) => {
  show_media.value = value;
};

const addFiles = (files) => {
  emit('addFiles', files);
  // Reset the file input value so the same file can be selected again
  if (upload_files.value) {
    upload_files.value.value = '';
  }
}

const deleteFile = (index) => {
  const file = props.files[index]
  emit(file.delete ? 'restoreFile' : 'deleteFile', index)
};

const ensureFileDataAvailable = async () => {
  // TODO: OBJECT STORAGE MIGRATION - Update for object storage URL validation
  // Check if temporary files stored in blob URLs are available
  // This can happen if the page is reloaded, when file is not available, but metadata is still there.

  if (!props.files) {
    return;
  }

  for (const [index, file] of props.files.entries()) {
    if (file.temp && file.path?.startsWith('blob:')) {
      try {
        const response = await fetch(file.path);
        if (!response.ok || !(await response.blob())) {
          emit('deleteFile', index);
        }
      } catch (error) {
        console.warn(`File ${file.name} is not accessible:`, error);
        emit('deleteFile', index);
      }
    }
  }
};

onMounted(() => {
  ensureFileDataAvailable();
});
</script>

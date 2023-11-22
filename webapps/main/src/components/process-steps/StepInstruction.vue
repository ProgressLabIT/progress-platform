<template>
  <div class="text-h5 text-uppercase q-mt-xl">
    {{ $t('phase.instruction_title') }}
  </div>

  <div class="row q-col-gutter-md q-mt-md">
    <div
      v-for="(media, index) in stepModel.media"
      :key="index"
      class="col-3 items-center column"
      :class="{ undraggable: !editMode }"
      @mouseenter="hoveredMediaIndex = index"
      @mouseleave="hoveredMediaIndex = null"
    >
      <q-card square bordered class="full-width">
        <!-- MEDIA TITLE -->
        <q-tooltip class="smaller text-center">
          {{ media.filename }}
        </q-tooltip>

        <q-img
          :src="media.src"
          ratio="1.7778"
          no-native-menu
          no-spinner
        >
          <template #error>
            <div class="row fit flex-center surface1">
              <q-icon
                size="xl"
                :name="media.filename.endsWith('.pdf') ? 'mdi-file-document-outline': 'mdi-error'"
                class="text-low"
              />
            </div>
          </template>
        </q-img>

        <div
          v-show="media.temp"
          class="absolute-top text-center smaller text-uppercase weight-bold"
          style="background-color: rgba(100, 100, 100, .8);"
        >
          {{ $capitalize($t('unsaved')) }}
        </div>
        <div
          v-show="media.trash"
          class="absolute-top text-center smaller text-uppercase weight-bold"
          style="background-color: rgba(231, 29, 54, .8);"
        >
          {{ $capitalize($t('phase.media_deleted')) }}
        </div>

        <div
          v-show="hoveredMediaIndex === index"
          class="absolute-full"
          style="background-color: #0007;"
        >
          <div class="row fit flex-center">
            <!-- SHOW MEDIA SCREEN -->
            <q-btn
              fab padding="xs"
              color="theme-grey"
              icon="mdi-magnify"
              class="q-mr-sm"
              @click.stop="showMedia(media)"
            />

            <template v-if="editMode">
              <!-- DELETE MEDIA -->
              <q-btn
                v-if="!media.trash"
                fab
                padding="xs"
                color="theme-red"
                icon="mdi-delete"
                @click.stop="deleteMedia(index)"
              />
              <!-- RESTORE MEDIA -->
              <q-btn
                v-else
                fab
                padding="xs"
                color="theme-orange"
                icon="mdi-upload"
                @click.stop="restoreMedia(index)"
              />
            </template>
          </div>
        </div>
      </q-card>

      <!-- TODO: Add media sorting using Sortable.js after implementing the backend logic (related CSS classes: .undraggable and .dragme) -->
      <!-- <q-icon
        v-if="editMode"
        name="mdi-drag-horizontal-variant"
        size="md"
        class="dragme"
      /> -->
    </div>

    <div class="col-3">
      <!-- TODO: Offer a way to browse existing media to select from, as an alternative to uploading a new one (?) -->
      <q-btn
        v-if="editMode"
        flat
        class="column flex-center q-pt-md q-pb-sm"
        style="cursor: pointer"
        @click="fileInputRef.click()"
      >
        <input
          ref="fileInputRef"
          type="file"
          multiple
          style="display: none"
          accept="image/*, application/pdf"
          @change="addMedia($event.target.files)"
        />
        <q-icon size="md" name="mdi-camera-plus" />
        <div class="q-mt-sm smaller">
          {{ $capitalize($t('phase.add_media')) }}
        </div>
      </q-btn>
    </div>
  </div>

  <MediaViewer
    :show="showMediaScreen"
    :media_name="selectedMedia?.filename"
    :media_src="selectedMedia?.src"
    @close="showMediaScreen = false"
  />
</template>

<script setup>
import { ref } from 'vue'

import MediaViewer from '@/components/MediaViewer.vue'

defineProps({
  editMode: {
    type: Boolean,
    required: true
  }
})
const stepModel = defineModel('step', { type: Object })

const fileInputRef = ref()

const selectedMedia = ref()
const hoveredMediaIndex = ref()
const showMediaScreen = ref(false)

function showMedia(media) {
  selectedMedia.value = media
  showMediaScreen.value = true
}

/**
 * @param {FileList} fileList
 */
function addMedia(fileList) {
  for (const file of fileList) {
    const objectUrl = URL.createObjectURL(file)

    stepModel.value.media.push({
      filename: file.name,
      src: objectUrl,
      data: file,
      temp: true,
      trash: false
    })
  }
}

function deleteMedia(index) {
  const media = stepModel.value.media[index]
  if (media.temp) {
    stepModel.value.media.splice(index, 1)
  } else {
    media.trash = true
  }
}

function restoreMedia(index) {
  const media = stepModel.value.media[index]
  media.trash = false
}
</script>

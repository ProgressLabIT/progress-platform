<template>
  <div class="row col-auto">

    <!-- INPUT -->
    <div class="col-12">
      <q-input
        for="search-input"
        v-model="inputText"
        filled
        autofocus
        dense
        clearable
        debounce="300"
        :label="props.label"
        icon="mdi-magnify"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>
    </div>

    <!-- SCAN -->
    <!-- <div class="col-auto">
      <q-btn
        class="full-height"
        color="primary"
        size="0.75rem"
        icon="mdi-barcode-scan"
        @click="show_code_scanner = true"
      >
      </q-btn>
    </div> -->

    <q-slide-transition>
      <ModalBottomContainer
        :show="show_code_scanner"
        @close="show_code_scanner = false"
      >
        <template #content>
          <CameraCodeScanner @scan="onScan" @load="onLoad"></CameraCodeScanner>
        </template>
      </ModalBottomContainer>
    </q-slide-transition>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import ModalBottomContainer from '@/components/ModalBottomContainer.vue';
import CameraCodeScanner from '@/components/barcode-reader/CameraCodeScanner.vue';
// import { useI18n } from 'vue-i18n';

// const $t = useI18n().t;
const props = defineProps({
  label: {
    type: String,
    default: () => undefined
  }
});
const inputText = defineModel({ type: String });
const show_code_scanner = ref(false);

function onLoad({ controls, scannerElement, browserMultiFormatReader }) {
  console.log(controls);
  console.log(scannerElement);
  console.log(browserMultiFormatReader);
}

function onScan({ result, raw }) {
  inputText.value = result;
  console.log(result);
  console.log(raw);
  show_code_scanner.value = false;
}
</script>

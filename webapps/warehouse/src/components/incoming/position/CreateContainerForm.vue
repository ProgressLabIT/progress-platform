<template>
  <q-scroll-area :visible="false" :style="form_height">
    <!-- SELECT TEMPLATE -->
    <template v-if="stage === 'select_template'">
      <q-list bordered separator>
        <q-item
          v-for="template in print_templates"
          :key="template._key"
          v-ripple
          clickable
          @click="selectTemplate(template)"
        >
          <q-item-label>{{ template.name }}</q-item-label>
        </q-item>
      </q-list>
    </template>

    <!-- SELECT COPIES -->
    <template v-else-if="stage === 'select_copies'">
      <div class="text-subtitle1 q-py-xl text-center">
        {{ $t('printLabel.selectCopiesTitle') }}
      </div>
      <div>
        <div ref="qtyarea" class="q-pa-md row justify-center">
          <q-card
            v-touch-repeat.mouse="handleRepeat"
            class="custom-area cursor-pointer bg-primary text-white shadow-2 relative-position row flex-center"
          >
            <div class="text-center">{{ selected_copies }}</div>
          </q-card>
        </div>
      </div>
      <div>
        <div class="fit row justify-center items-start content-center">
          <q-btn
            color="theme-blue"
            :label="$t('back')"
            class="col-6"
            @click="stage = 'select_template'"
          ></q-btn>
          <q-btn
            color="theme-blue"
            :label="$t('next')"
            class="col-6"
            @click="selectCopies()"
          ></q-btn>
        </div>
      </div>
    </template>

    <!-- SELECT PRINTER -->
    <template v-else-if="stage === 'select_printer'">
      <q-list bordered separator>
        <q-item
          v-for="printer in printers"
          :key="printer._key"
          v-ripple
          clickable
          @click="selectPrinter(printer)"
        >
          <q-item-label>{{ printer.name }}</q-item-label>
          <q-item-label caption>{{ printer.description }}</q-item-label>
        </q-item>
      </q-list>
    </template>

    <!-- PRINTING -->
    <template v-else-if="stage === 'printing'">
      <q-inner-loading
        :showing="stage === 'printing'"
        label="Printing..."
        label-class="text-teal"
        label-style="font-size: 1.1em"
      />
    </template>

    <!-- PRINT_DONE -->
    <template v-else-if="stage === 'print_done'">
      <div class="text-subtitle1 q-py-xl text-center">Print done!</div>
    </template>

    <div class="fit row justify-center items-start content-center">
      <q-btn
        v-if="stage !== 'printing'"
        color="theme-blue"
        :label="stage === 'print_done' ? $t('close') : $t('cancel')"
        class="col-12"
        @click="closeForm()"
      ></q-btn>
    </div>
  </q-scroll-area>
</template>

<script>
export default {
  name: 'CreateContainerForm',

  props: {
    availableHeight: {
      type: Number,
      required: true,
    },
  },

  data() {
    return {
      stage: 'select_template',
      selected_template: undefined,
      selected_copies: 0,
      selected_printers: undefined,
    };
  },

  computed: {
    form_height() {
      return 'height: ' + (this.availableHeight - 30) + 'px';
    },
  },

  mounted() {
    this.stage = 'select_template';
  },

  beforeUnmount() {
    this.$bus.emit('close-footer');
  },

  methods: {
    closeForm() {
      this.$bus.emit('close-footer');
    },

    handleRepeat(info) {
      let qtyRect = this.$refs.qtyarea.getBoundingClientRect();
      if (info.position.left > qtyRect.x + qtyRect.width / 2) {
        this.selected_copies++;
      } else if (this.selected_copies > 0) {
        this.selected_copies--;
      }
    },

    selectTemplate(template) {
      this.selected_template = template;
      this.stage = 'select_copies';
    },

    selectCopies() {
      this.stage = 'select_printer';
    },

    selectPrinter(printer) {
      this.selected_printers = printer;
      this.stage = 'printing';

      setTimeout(() => {
        this.stage = 'print_done';
      }, 3000);
    },
  },
};
</script>

<style lang="sass" scoped>
.custom-area
  width: 76%
  height: 100px
  border-radius: 3px
  padding: 8px
</style>

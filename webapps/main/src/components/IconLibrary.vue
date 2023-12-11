<template>
  <div id="icons">
    <slot name="input">
      <q-input
        v-model="search_text"
        :label="$capitalize($t('search'))"
        icon="mdi-magnify"
        debounce="300"
        dense
        square
        filled
        class="full-width q-mb-lg"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>
    </slot>

    <slot name="content">
      <q-virtual-scroll
        style="max-height: 400px"
        :items="icon_rows"
        v-slot="{ item, index }"
      >
        <div class="row text-body2 smaller justify-center" :key="index" dense>
          <div
            v-for="icon in item"
            :key="icon"
            class="col-1 text-center icon flex flex-center q-pa-md"
            @click="choose(icon)"
          >
            <q-icon :name="icon" :size="icon_size">
              <q-tooltip>
                {{ icon }}
              </q-tooltip>
            </q-icon>
          </div>
        </div>
      </q-virtual-scroll>
    </slot>
  </div>
</template>

<script>
export default {
  name: 'IconLibrary',

  props: {
    icons_per_row: {
      type: Number,
      default: 12,
    },
    icon_size: {
      type: String,
      default: 'xs',
    },
  },

  emits: ['choice', 'hide'],

  data() {
    return {
      search_text: '',
    };
  },

  computed: {
    icons() {
      return this.$store.state.icons.filter((i) =>
        i.includes(this.search_text),
      );
    },

    icon_rows() {
      let list = [];
      const how_many_rows = Math.ceil(this.icons.length / this.icons_per_row);
      for (let row = 0; row <= how_many_rows; row++) {
        const first_icon_index = row * this.icons_per_row;
        const last_icon_index = first_icon_index + this.icons_per_row;
        list.push(this.icons.slice(first_icon_index, last_icon_index));
      }
      return Object.freeze(list);
    },
  },

  methods: {
    choose(icon) {
      this.$emit('choice', icon);
      this.$emit('hide'); // for use within BaseDialog
    },
  },
};
</script>

<style lang="sass" scoped>
.icon:hover
  background-color: var(--hover-bg-blue)
  cursor: pointer
</style>

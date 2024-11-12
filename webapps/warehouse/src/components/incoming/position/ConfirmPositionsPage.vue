<template>
  <template v-if="positions.length === 1">
    <div
      class="row justify-center items-start content-left"
      style="height: 100px"
    >
      <div class="col-10">{{ $t('incoming.position_caption') }}</div>
      <div class="col-2">
        {{ $t('incoming.quantity_caption') }}
      </div>
      <div class="col-10">{{ positions[0].code }}</div>
      <div class="col-2">
        {{ positions[0].quantity }}
      </div>
    </div>
  </template>
  <template v-else>
    <q-slider
      v-for="position in positions"
      :key="position._key"
      v-model="position.quantity"
      class="q-mt-lg"
      :min="0"
      :max="quantity"
      :step="1"
      label
      :label-value="value"
      label-always
      @change="adjust(position)"
    />
    <div
      class="row justify-center items-start content-left"
      style="height: 100px"
    >
      <div class="col-10">{{ $t('incoming.position_caption') }}</div>
      <div class="col-2">
        {{ $t('incoming.quantity_caption') }}
      </div>
      <div v-for="position in positions" :key="position._key">
        <div class="col-10">{{ position.code }}</div>
        <div class="col-2">
          {{ position.quantity }}
        </div>
      </div>
    </div>
  </template>

  <div class="fit row justify-center items-start content-center">
    <q-btn
      color="theme-blue"
      :label="$t('incoming.confirm_and_close')"
      class="col-12"
      @click="$emit('positionConfirmed', 'true')"
    ></q-btn>
    <q-btn
      color="theme-blue"
      :label="$t('incoming.confirm_and_start_again')"
      class="col-12"
      @click="$emit('positionConfirmed', 'false')"
    ></q-btn>
    <q-btn
      color="theme-blue"
      :label="$t('cancel')"
      class="col-12"
      @click="$emit('back')"
    ></q-btn>
  </div>
</template>

<script>
export default {
  name: 'ConfirmPositionsPage',

  props: {
    quantity: {
      type: Number,
      required: true,
    },
    positions: {
      type: Array,
      required: true,
    },
  },

  emits: ['positionConfirmed', 'back'],

  data() {
    return {
      show_code_scanner: false,
      loading: false,
      last_research: undefined,
    };
  },

  methods: {
    adjust(position) {
      let quantity_to_adjust = this.quantity;
      for (const pos of this.positions) {
        quantity_to_adjust -= pos.quantity;
      }

      let position_index = this.positions.findIndex(
        (pos) => pos._key === position._key
      );

      let next_index = position_index + 1;

      while (quantity_to_adjust !== 0) {
        if (next_index === this.positions.length) {
          next_index = 0;
        }
        let next_position = this.positions[next_index];
        if (quantity_to_adjust > 0) {
          if (!next_position.locked) {
            next_position.quantity += quantity_to_adjust;
            quantity_to_adjust = 0;
          }
          next_index += 1;
        } else {
          let adjustment = 0 - quantity_to_adjust;
          let possible_adjustment =
            next_position.quantity - adjustment >= 0
              ? adjustment
              : next_position.quantity;
          if (!next_position.locked) {
            next_position.quantity -= possible_adjustment;
            quantity_to_adjust += possible_adjustment;
          }
          next_index += 1;
        }
      }
    },
  },
};
</script>

<style lang="sass">
.grid-style-transition
  transition: transform .28s, background-color .28s
</style>

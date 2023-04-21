<template>
  <BaseActionCard
    title="NEW FIELD"
    @save="addField"
    @cancel="$emit('close')">

    <div
      v-for="prop in Object.keys(new_field)"
      class="q-my-md">

      <!-- TYPE -->
      <template v-if="prop == 'type'">
        <q-select
          filled
          :label="$t('type')"
          :options="field_types"
          v-model="new_field.type"
          emit-value
          map-options>
          <template #option="scope">
            <q-item v-bind="scope.itemProps">
              <q-item-section avatar>
                <q-icon :name="scope.opt.icon" />
              </q-item-section>
              <q-item-section>
                <q-item-label>
                  {{ scope.opt.label }}
                </q-item-label>
              </q-item-section>
            </q-item>
          </template>
        </q-select>
      </template>

      <template v-else>
        <q-input
          filled
          autogrow
          :label="$t(prop)"
          v-model="new_field[prop]">
        </q-input>
      </template>

    </div>

  </BaseActionCard>
</template>

<script>
import BaseActionCard from '@/components/BaseActionCard.vue'
import form from '@/mixins/form.js'

export default {

  name: 'CustomFieldNew',

  components: {
    BaseActionCard
  },

  mixins: [form],

  data () {
    return {
      new_field: {
        type: null,
        name: null,
        label: null,
        hint: null
      },
    }
  },

  methods: {
    addField() {
      const data = {
        type: this.new_field.type,
        name: this.new_field.name,
        default_label: this.new_field.label,
        default_hint: this.new_field.hint
      }
      this.$api.post('field', data).then(() => this.$emit('close'))
    }
  }
}
</script>

<style lang="css" scoped>
</style>

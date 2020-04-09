<template>
    <v-list-item>

      <v-list-item-avatar v-if="src">
        <slot name="avatar">
          <v-img :src="src">
            <template v-slot:placeholder>
              <slot name="placeholder"></slot>
            </template>
          </v-img>
        </slot>
      </v-list-item-avatar>
      
      <v-list-item-content>
        <v-list-item-title class="highlight">
          <slot name="title">
              {{ title }}
          </slot>
        </v-list-item-title>
        
        <v-list-item-subtitle class="body-2">
          <slot name="subtitle">
              {{ subtitle }}
          </slot>
        </v-list-item-subtitle>
      </v-list-item-content>
      
      <v-list-item-action v-if="edit">
        <slot name="actions">
          <BaseTooltipIcon
            :icon="icon"
            :tooltip="tooltip"
            :color="color"
            @iconClick="emit">
          </BaseTooltipIcon>
        </slot>
      </v-list-item-action>

    </v-list-item>
</template>

<script>
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'

export default {

  name: 'BaseAvatarListElement',

  props: { 
    src: String,
    title: String, 
    subtitle: String, 
    edit: Boolean,
    icon: {
      type: String, 
      default: 'close'
    },
    tooltip: String,
    color: String,
  },

  components: {BaseTooltipIcon},

  methods: {
    emit() {
      this.$emit('iconClick')
    },
  }
}
</script>

<style lang="css" scoped>
</style>
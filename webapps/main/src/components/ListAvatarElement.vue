<template>
    <v-list-item>

      <v-list-item-avatar v-if="src">
        <slot name="avatar">
          <v-img :src="src"></v-img>
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
          <TooltipIcon
            :icon="icon"
            :tooltip="tooltip"
            :color="color"
            @iconClick="emit">
          </TooltipIcon>
        </slot>
      </v-list-item-action>

    </v-list-item>
</template>

<script>
import TooltipIcon from '@/components/TooltipIcon.vue'

export default {

  name: 'ListAvatarElement',

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

  components: {TooltipIcon},

  methods: {
    emit() {
      this.$emit('iconClick')
    }
  }
}
</script>

<style lang="css" scoped>
</style>
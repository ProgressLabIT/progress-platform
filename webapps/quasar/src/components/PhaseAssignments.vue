<template>
  <v-container class="fill">
    <v-row class="fill-height">
      <v-col cols="4" class="px-10 py-6 d-flex flex-column fill-height">
        <h5 class="text-uppercase mb-8">
          {{ $tc("equipment", 2) }}
        </h5>
        <div class="fill-height scroll">
          <v-list two-line>

            <v-subheader>
              {{ $tc("equipment_class", 2) | capitalize }}
            </v-subheader>
            
            <BaseAvatarListElement 
              v-for="ec in assigned_eq_classes" :key="ec._id"
              :src="`/media/equipment/${ec.src}`"
              :title="ec.name"
              :subtitle="$tc('equipment_class', 1) | capitalize"
              :edit="edit_mode"
              :tooltip="$tc('remove_assignment') | capitalize"
              :color="$theme.red"
              icon="close"
              @iconClick="cancelAssignment(ec._id)">
            </BaseAvatarListElement>

            <v-divider class="mt-2 mb-3"></v-divider>
            
            <v-subheader>Attrezzature</v-subheader>

            <BaseAvatarListElement
              v-for="e in assigned_equipment" :key="e._id"
              :src="`/media/equipment/${e.src}`"
              :title="e.name"
              :subtitle="e.class"
              :edit="edit_mode"
              :tooltip="$tc('remove_assignment') | capitalize"
              :color="$theme.red"
              icon="close"
              @iconClick="cancelAssignment(e._id)">
            </BaseAvatarListElement>

          </v-list>
        </div>

        <v-autocomplete
          ref="assign_equipment"
          v-if="edit_mode"
          v-model="new_assignment"
          :items="add_equipment_list"
          item-value="_id"
          item-text="name"
          single-line hide-details
          return-object
          :label="$tc('add_equipment') | capitalize"
          :menu-props="{ top: true, offsetY: true }"
          class="mt-auto flex-grow-0"
          @input="addAssignment($event)"
          @blur="new_assignment = null"
          >
          <template v-slot:item="{ item }">
            <BaseAvatarListElement
              :src="`/media/equipment/${item.src}`"
              :title="item.name"
              :subtitle="item.class">
            </BaseAvatarListElement>
          </template>
        </v-autocomplete>


      </v-col> 
      <v-divider vertical inset></v-divider>
      <v-col class="px-10 py-6 d-flex flex-column fill-height">
        <h5 class="text-uppercase mb-8">
          {{ $tc('personnel') | capitalize }}
        </h5>

        <div class="fill-height scroll">
          <v-subheader>
            {{ $tc('department', 2) | capitalize }}
          </v-subheader>
          
          <v-row>
            <v-col cols="auto"
              v-for="d in assigned_departments" :key="d._id">
              <BaseAvatarListElement 
                :src="null"
                :title="d.name"
                :subtitle="$tc('department', 1) | capitalize"
                :edit="edit_mode"
                :tooltip="$tc('remove_assignment') | capitalize"
                :color="$theme.red"
                icon="close"
                @iconClick="cancelAssignment(d._id)">
              </BaseAvatarListElement>
            </v-col>
          </v-row>          

          <v-divider class="mb-3"></v-divider>
          
          <v-subheader>
            {{ $tc('operator', 2) | capitalize }}
          </v-subheader>

          <v-row >
            <v-col cols="auto" 
              v-for="o in assigned_operators" :key="o._id"
              class="flex-shrink-1">   
              <BaseAvatarListElement
                :src="`/media/user/${o.src}`"
                :title="o.name"
                :subtitle="operatorDepartmentName(o.department)"
                :edit="edit_mode"
                :tooltip="$tc('remove_assignment') | capitalize"
                :color="$theme.red"
                icon="close"
                @iconClick="cancelAssignment(o._id)">
              </BaseAvatarListElement>
            </v-col>

          </v-row>

        </div>

        <v-autocomplete
          ref="assign_operator"
          v-if="edit_mode"
          v-model="new_assignment"
          :items="add_operator_list"
          item-value="_id"
          item-text="name"
          single-line hide-details
          return-object
          :label="$tc('add_operator', 2)"
          :menu-props="{ top: true, offsetY: true }"
          class="mt-auto flex-grow-0"
          @input="addAssignment($event)"
          @blur="new_assignment = null"
          >
          <template v-slot:item="{ item }">
            <BaseAvatarListElement
              :src="`/media/user/${item.src}`"
              :title="item.name"
              :subtitle="item.class">
            </BaseAvatarListElement>
          </template>
        </v-autocomplete>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import BaseAvatarListElement from '@/components/BaseAvatarListElement'

export default {

  name: 'PhaseAssignments',

  props: ['phase', 'edit_mode', 'product_data'],

  components: {
    BaseAvatarListElement
  },

  data () {
    return {
      equipment_classes: [
        { _id: 'ec/1', name: 'Linea Juki', src: 'Juki_line.jpg'},
        { _id: 'ec/2', name: 'Linea Fuji', src: 'Fuji_line.jpeg'},
      ],
      equipment: [
        { _id: 'e/a', class: 'Linea Juki', name: 'Juki Line 1', src: 'Juki_line.jpg' },
        { _id: 'e/b', class: 'Linea Juki', name: 'Juki Line 2', src: 'Juki_line.jpg' },
        { _id: 'e/c', class: 'Linea Juki', name: 'Juki Line 3', src: 'Juki_line.jpg' },
        { _id: 'e/d', class: 'Linea Fuji', name: 'Fuji Line 1', src: 'Fuji_line.jpeg' },
        { _id: 'e/e', class: 'Linea Fuji', name: 'Fuji Line 2', src: 'Fuji_line.jpeg' },
        { _id: 'e/f', class: null, name: 'SPI', src: 'spi.gif' },
        { _id: 'e/g', class: null, name: 'AOI', src: 'aoi.png' },
        { _id: 'e/h', class: null, name: 'X-Ray', src: 'x-ray.jpg' },
      ],
      operators: [
        { _id: 'o/1', name: 'Jared Blue', department: 'd/1', src: 'Jared_Blue.jpg' },
        { _id: 'o/2', name: 'Thomas Grey', department: 'd/3', src: 'Thomas_Grey.jpg' },
        { _id: 'o/3', name: 'Robert Green', department: 'd/1', src: 'Robert_Green.jpg' },
        { _id: 'o/4', name: 'Dana Teal', department: 'd/2', src: 'Dana_Teal.jpg' },
        { _id: 'o/5', name: 'Jean Pink', department: 'd/2', src: 'Jean_Pink.jpg' },
        { _id: 'o/6', name: 'Kristy Rose', department: 'd/3', src: 'Kristy_Rose.jpg' },
        { _id: 'o/7', name: 'Marcus Cobalt', department: 'd/4', src: 'Marcus_Cobalt.jpg' },
        { _id: 'o/8', name: 'Megan Brown', department: 'd/1', src: 'Megan_Brown.jpg' },
        { _id: 'o/9', name: 'Pauline Gold', department: 'd/2', src: 'Pauline_Gold.jpg' }
      ],
      departments: [
        { _id: 'd/1', name: 'SMT' },
        { _id: 'd/2', name: 'THT' },
        { _id: 'd/3', name: 'Warehouse' },
        { _id: 'd/4', name: 'QA' },
      ],
      assignments: {
        equipment_classes: ['ec/2'],
        equipment: ['e/a', 'e/b'],
        departments: ['d/1'],
        operators: ['o/1','o/3'] 
      },

      id_root_map: {
        'ec': 'equipment_classes',
        'e': 'equipment',
        'o': 'operators',
        'd': 'departments',
      },

      new_assignment: null,
    }
  },

  computed: {
    assigned_operators() {
      return this.operators.filter(o => this.assignments.operators.includes(o._id))
    },

    assigned_departments() {
      return this.departments.filter(d => this.assignments.departments.includes(d._id))
    },

    assigned_eq_classes() {
      return this.equipment_classes.filter(ec => this.assignments.equipment_classes.includes(ec._id))
    },

    assigned_equipment() {
      return this.equipment.filter(e => this.assignments.equipment.includes(e._id))
    },

    add_equipment_list() {
      return [
        { header: this.capitalize(this.$tc('equipment_class', 2) },
        ...this.equipment_classes.map(c => { 
          return {
             ...c, 
             'class': this.capitalize(this.$tc('equipment_class', 1))
          } 
        }),
        { divider: true },
        { header: this.capitalize(this.$tc('equipment')) },
        ...this.equipment.map( e => {
          return {
            ...e,
            'class': e.class ? e.class : this.capitalize($tc('no_class'))
          }
        })
      ]
    },

    add_operator_list() {
      return [
        { header: this.capitalize($tc('department', 2)) },
        ...this.departments.map(d => { 
          return {
             ...d, 
             'department': this.capitalize($tc('department', 1))
          } 
        }),
        { divider: true },
        { header: this.capitalize($tc('operator', 2)) },
        ...this.operators.map( o => {
          return {
            ...o,
            'department': o.department ? o.department : this.capitalize($tc('no_department'))
          }
        })
      ]
    },
  },

  methods: {
    capitalize(string) {
      return this.$options.filters.capitalize(string)
    },

    operatorDepartmentName(dep_id) {
      return this.departments.find(d => d._id == dep_id).name
    },

    addAssignment(assignee) {

      const assignment_list_name = this.id_root_map[assignee._id.split("/")[0]]

      this.assignments[assignment_list_name].push(assignee._id)
      
      setTimeout(() => {
        this.new_assignment = null
        this.$refs.assign_equipment.blur()
        this.$refs.assign_operator.blur()
      }, 1)
    },

    cancelAssignment(assignee_id) {
      const assignment_list_name = this.id_root_map[assignee_id.split("/")[0]]
      let assignment_list = this.assignments[assignment_list_name]
      const assignment_index = assignment_list.indexOf(assignee_id)
      assignment_list.splice(assignment_index, 1)
    }
  },
}
</script>

<style lang="css" scoped>

</style>
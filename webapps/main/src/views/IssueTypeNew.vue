<template>
  <BaseModalForm
    id="new-issue-type-form"
    :show="true"
    :loading="saving"
    max-width="700px"
    @submit="submit"
    @cancel="$router.back()"
  >
    <template #title>
      {{ $t('issue_type_new') }}
    </template>

    <template #form>
      <div class="row q-col-gutter-lg items-center" style="min-width: 400px">
        <div class="col-6">
          <q-input
            v-model="new_issue_type.name"
            filled
            stack-label
            :label="$capitalize($t('name').toUpperCase())"
          >
          </q-input>
        </div>

        <div class="col-3 text-uppercase">
          <q-input
            v-model="new_issue_type.code"
            filled
            stack-label
            :label="$t('code').toUpperCase()"
          >
          </q-input>
        </div>

        <div class="col-3 text-uppercase">
          <q-toggle
            v-model="new_issue_type.critical"
            :label="$t('critical').toUpperCase()"
          >
          </q-toggle>
        </div>

        <!--  <div class="col-3 text-uppercase">
          <q-input
            filled
            stack-label
            :label="$t('close_within')"
            type="number"
            min="0"
            v-model.number="new_issue_type.close_within">
          </q-input>
        </div>

        <div class="col-9 text-low">
          {{ $t('issue_type_close_within_explainer') }}
        </div>
 -->
        <div class="col-12">
          <q-input
            v-model="new_issue_type.description"
            filled
            stack-label
            autogrow
            clearable
            :label="$t('description').toUpperCase()"
          >
          </q-input>
        </div>

        <div class="row items-center justify-between full-width">
          <div class="text-h5 text-high text-uppercase">
            {{ $t('icon') }}
          </div>
          <div class="text-low row items-center">
            <q-icon :name="new_issue_type.icon" size="lg" class="q-mr-sm" />
            <div class="text-body2 text-italic">{{ new_issue_type.icon }}</div>
          </div>
          <q-btn
            flat
            :label="$t('change')"
            color="theme-blue"
            @click="show_icon_library = true"
          >
          </q-btn>
          <BaseDialog :show="show_icon_library">
            <div class="surface2 q-pa-md">
              <IconLibrary @choice="(value) => pickIcon(value)" />
            </div>
          </BaseDialog>
        </div>
      </div>
    </template>
  </BaseModalForm>
</template>

<script>
import BaseDialog from '@/components/BaseDialog.vue';
import BaseModalForm from '@/components/BaseModalForm.vue';
import IconLibrary from '@/components/IconLibrary.vue';

export default {
  name: 'IssueTypeNew',

  components: {
    BaseModalForm,
    BaseDialog,
    IconLibrary,
  },

  data() {
    return {
      saving: false,
      show_icon_library: false,
      new_issue_type: {
        name: undefined,
        code: undefined,
        description: undefined,
        critical: false,
        close_within: 0,
        icon: 'mdi-alert-circle',
      },
    };
  },

  methods: {
    pickIcon(value) {
      this.new_issue_type.icon = value;
      this.show_icon_library = false;
    },

    submit() {
      this.saving = true;
      if (!this.new_issue_type.name) {
        window.alert(
          this.$capitalize(this.$t('issue_type_alerts_name_missing')),
        );
      } else {
        this.$store
          .dispatch('createIssueType', this.new_issue_type)
          .then((new_issue_type_key) => {
            this.$router.push({
              name: 'issueTypeDetail',
              params: {
                issueTypeKey: new_issue_type_key,
              },
            });
          })
          .catch((err) => {
            if (err.response.status === 409) {
              window.alert(
                this.$capitalize(
                  this.$t('issue_type_alerts_name_or_code_used'),
                ),
              );
            } else {
              window.alert(err);
            }
          });
      }
    },
  },
};
</script>

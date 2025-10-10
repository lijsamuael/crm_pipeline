<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('Create Pipeline') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager() && !isMobileView"
              variant="ghost"
              class="w-7"
              :tooltip="__('Edit fields layout')"
              :icon="EditIcon"
              @click="openQuickEntryModal"
            />
            <Button
              variant="ghost"
              class="w-7"
              @click="show = false"
              icon="x"
            />
          </div>
        </div>
        <div>
          <FieldLayout v-if="tabs.data" :tabs="tabs.data" :data="pipeline.doc" />
          <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="__('Create')"
            :loading="isPipelineCreating"
            @click="createNewPipeline"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { sessionStore } from '@/stores/session'
import { isMobileView } from '@/composables/settings'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { capture } from '@/telemetry'
import { createResource } from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { useDocument } from '@/data/document'
import { computed, onMounted, ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  defaults: Object,
})

const { user } = sessionStore()
const { getUser, isManager } = usersStore()
const { getPipelineStatus, statusOptions } = statusesStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')

const show = defineModel()
const router = useRouter()
const error = ref(null)
const isPipelineCreating = ref(false)

const { document: pipeline, triggerOnBeforeCreate } = useDocument('CRM Pipeline')

const pipelineStatuses = computed(() => {
  let statuses = statusOptions('pipeline')
  if (!pipeline.doc.status) {
    pipeline.doc.status = statuses?.[0]?.value
  }
  return statuses
})

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Pipeline'],
  params: { doctype: 'CRM Pipeline', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    return _tabs.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          column.fields.forEach((field) => {
            if (field.fieldname == 'status') {
              field.fieldtype = 'Select'
              field.options = pipelineStatuses.value
              field.prefix = getPipelineStatus(pipeline.doc.status).color
            }

            if (field.fieldtype === 'Table') {
              pipeline.doc[field.fieldname] = []
            }
          })
        })
      })
    })
  },
})

const createPipeline = createResource({
  url: 'frappe.client.insert',
})

async function createNewPipeline() {
  if (pipeline.doc.website && !pipeline.doc.website.startsWith('http')) {
    pipeline.doc.website = 'https://' + pipeline.doc.website
  }

  await triggerOnBeforeCreate?.()

  createPipeline.submit(
    {
      doc: {
        doctype: 'CRM Pipeline',
        ...pipeline.doc,
      },
    },
    {
      validate() {
        error.value = null
        if (!pipeline.doc.pipeline_name) {
          error.value = __('Pipeline Name is mandatory')
          return error.value
        }
        if (pipeline.doc.annual_revenue) {
          if (typeof pipeline.doc.annual_revenue === 'string') {
            pipeline.doc.annual_revenue = pipeline.doc.annual_revenue.replace(/,/g, '')
          } else if (isNaN(pipeline.doc.annual_revenue)) {
            error.value = __('Annual Revenue should be a number')
            return error.value
          }
        }
        if (
          pipeline.doc.mobile_no &&
          isNaN(pipeline.doc.mobile_no.replace(/[-+() ]/g, ''))
        ) {
          error.value = __('Mobile No should be a number')
          return error.value
        }
        if (pipeline.doc.email && !pipeline.doc.email.includes('@')) {
          error.value = __('Invalid Email')
          return error.value
        }
        if (!pipeline.doc.status) {
          error.value = __('Status is required')
          return error.value
        }
        isPipelineCreating.value = true
      },
      onSuccess(data) {
        capture('pipeline_created')
        isPipelineCreating.value = false
        show.value = false
        router.push({ name: 'Pipeline', params: { pipelineId: data.name } })
        updateOnboardingStep('create_first_pipeline', true, false, () => {
          localStorage.setItem('firstPipeline' + user, data.name)
        })
      },
      onError(err) {
        isPipelineCreating.value = false
        if (!err.messages) {
          error.value = err.message
          return
        }
        error.value = err.messages.join('\n')
      },
    },
  )
}

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'CRM Pipeline' }
  nextTick(() => (show.value = false))
}

onMounted(() => {
  pipeline.doc = { no_of_employees: '1-10' }
  Object.assign(pipeline.doc, props.defaults)

  if (!pipeline.doc?.pipeline_owner) {
    pipeline.doc.pipeline_owner = getUser().name
  }
  if (!pipeline.doc?.status && pipelineStatuses.value[0]?.value) {
    pipeline.doc.status = pipelineStatuses.value[0].value
  }
})
</script>
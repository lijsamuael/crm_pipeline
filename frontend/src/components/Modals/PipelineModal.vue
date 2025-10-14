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

// Get pipeline statuses
const pipelineStatuses = computed(() => {
  try {
    let statuses = statusOptions('pipeline') || []
    if (statuses.length === 0) {
      // Fallback statuses if none are defined
      statuses = [
        { value: 'Open', label: 'Open' },
        { value: 'In Progress', label: 'In Progress' },
        { value: 'Completed', label: 'Completed' }
      ]
    }
    return statuses
  } catch (error) {
    console.warn('Error getting pipeline statuses:', error)
    return [
      { value: 'Open', label: 'Open' },
      { value: 'In Progress', label: 'In Progress' },
      { value: 'Completed', label: 'Completed' }
    ]
  }
})

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Pipeline'],
  params: { doctype: 'CRM Pipeline', type: 'Quick Entry' },
  auto: true,
  transform: (tabs) => {
    if (!tabs || !Array.isArray(tabs)) return tabs
    
    return tabs.map((tab) => {
      if (!tab.sections) return tab
      
      return {
        ...tab,
        sections: tab.sections.map((section) => {
          if (!section.columns) return section
          
          return {
            ...section,
            columns: section.columns.map((column) => {
              if (!column.fields) return column
              
              return {
                ...column,
                fields: column.fields.map((field) => {
                  // Handle status field
                  if (field.fieldname === 'status') {
                    return {
                      ...field,
                      fieldtype: 'Select',
                      options: pipelineStatuses.value,
                      prefix: pipeline.doc.status ? getPipelineStatus(pipeline.doc.status)?.color : 'gray'
                    }
                  }
                  
                  // Handle table fields
                  if (field.fieldtype === 'Table' && !pipeline.doc[field.fieldname]) {
                    pipeline.doc[field.fieldname] = []
                  }
                  
                  return field
                })
              }
            })
          }
        })
      }
    })
  }
})

const createPipeline = createResource({
  url: 'frappe.client.insert',
  makeParams: (params) => params
})

async function createNewPipeline() {
  // Reset error
  error.value = null
  
  // Validate required fields
  if (!pipeline.doc.pipeline_name) {
    error.value = __('Pipeline Name is mandatory')
    return
  }
  
  if (!pipeline.doc.status) {
    error.value = __('Status is required')
    return
  }

  // Validate email if provided
  if (pipeline.doc.email && !isValidEmail(pipeline.doc.email)) {
    error.value = __('Invalid Email')
    return
  }

  // Validate website format
  if (pipeline.doc.website && !pipeline.doc.website.startsWith('http')) {
    pipeline.doc.website = 'https://' + pipeline.doc.website
  }

  // Validate numeric fields
  if (pipeline.doc.annual_revenue) {
    const revenue = parseFloat(pipeline.doc.annual_revenue.toString().replace(/,/g, ''))
    if (isNaN(revenue)) {
      error.value = __('Annual Revenue should be a number')
      return
    }
    pipeline.doc.annual_revenue = revenue
  }

  // Validate mobile number
  if (pipeline.doc.mobile_no && !isValidPhoneNumber(pipeline.doc.mobile_no)) {
    error.value = __('Mobile No should be a valid number')
    return
  }

  // Trigger any before-create hooks
  await triggerOnBeforeCreate?.()

  isPipelineCreating.value = true

  try {
    const result = await createPipeline.submit({
      doc: {
        doctype: 'CRM Pipeline',
        ...pipeline.doc,
      }
    })

    capture('pipeline_created')
    isPipelineCreating.value = false
    show.value = false
    
    // Navigate to the new pipeline
    router.push({ name: 'Pipeline', params: { pipelineId: result.name } })
    
    // Update onboarding
    updateOnboardingStep('create_first_pipeline', true, false, () => {
      localStorage.setItem('firstPipeline' + user, result.name)
    })
    
  } catch (err) {
    isPipelineCreating.value = false
    console.error('Error creating pipeline:', err)
    
    if (err.messages) {
      error.value = err.messages.join('\n')
    } else if (err.message) {
      error.value = err.message
    } else {
      error.value = __('Failed to create pipeline. Please try again.')
    }
  }
}

// Helper functions for validation
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

function isValidPhoneNumber(phone) {
  // Basic phone validation - allows numbers, spaces, hyphens, parentheses, and +
  const phoneRegex = /^[\d\s\-+()]+$/
  return phoneRegex.test(phone)
}

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'CRM Pipeline' }
  nextTick(() => (show.value = false))
}

onMounted(() => {
  // Initialize pipeline with default values
  pipeline.doc = { 
    no_of_employees: '1-10',
    status: pipelineStatuses.value[0]?.value || 'Open'
  }
  
  // Apply any provided defaults
  Object.assign(pipeline.doc, props.defaults)

  // Set default pipeline owner
  if (!pipeline.doc?.pipeline_owner) {
    pipeline.doc.pipeline_owner = getUser().name
  }
  
  // Ensure status is set
  if (!pipeline.doc?.status && pipelineStatuses.value[0]?.value) {
    pipeline.doc.status = pipelineStatuses.value[0].value
  }
})
</script>
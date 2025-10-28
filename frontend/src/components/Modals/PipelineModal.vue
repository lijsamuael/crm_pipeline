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
          <div
            v-if="hasOrganizationSections || hasContactSections"
            class="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-3"
          >
            <div
              v-if="hasOrganizationSections"
              class="flex items-center gap-3 text-sm text-ink-gray-5"
            >
              <div>{{ __('Choose Existing Organization') }}</div>
              <Switch v-model="chooseExistingOrganization" />
            </div>
            <div
              v-if="hasContactSections"
              class="flex items-center gap-3 text-sm text-ink-gray-5"
            >
              <div>{{ __('Choose Existing Contact') }}</div>
              <Switch v-model="chooseExistingContact" />
            </div>
          </div>
          <div
            v-if="hasOrganizationSections || hasContactSections"
            class="h-px w-full border-t my-5"
          />
          <FieldLayout
            ref="fieldLayoutRef"
            v-if="tabs.data?.length"
            :tabs="tabs.data"
            :data="pipeline.doc"
            doctype="CRM Pipeline"
          />
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
import { Switch, createResource } from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { useDocument } from '@/data/document'
import { computed, onMounted, ref, nextTick, watch } from 'vue'
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

const hasOrganizationSections = ref(true)
const hasContactSections = ref(true)

const chooseExistingContact = ref(false)
const chooseExistingOrganization = ref(false)
const fieldLayoutRef = ref(null)

watch(
  [chooseExistingOrganization, chooseExistingContact],
  ([organization, contact]) => {
    if (!tabs.data) return
    
    tabs.data.forEach((tab) => {
      tab.sections.forEach((section) => {
        if (section.name === 'organization_section') {
          section.hidden = !organization
        } else if (section.name === 'organization_details_section') {
          section.hidden = organization
        } else if (section.name === 'contact_section') {
          section.hidden = !contact
        } else if (section.name === 'contact_details_section') {
          section.hidden = contact
        }
      })
    })

    // Set pipeline_type to "Default" when selecting existing contact or organization
    if (organization || contact) {
      pipeline.doc.pipeline_type = 'Default'
    }
  },
)

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
    if (!_tabs) return _tabs
    
    hasOrganizationSections.value = false
    hasContactSections.value = false
    
    // Properly transform the tabs without mutating the original
    const transformedTabs = _tabs.map((tab) => {
      const sections = tab.sections?.map((section) => {
        const columns = section.columns?.map((column) => {
          const fields = column.fields?.map((field) => {
            // Initialize the field value in pipeline.doc if it doesn't exist
            if (field.fieldname && !(field.fieldname in pipeline.doc)) {
              // Set empty string for regular fields, empty array for table fields
              if (field.fieldtype === 'Table') {
                pipeline.doc[field.fieldname] = []
              } else {
                pipeline.doc[field.fieldname] = ''
              }
            }

            // Check for organization and contact sections
            if (
              ['organization_section', 'organization_details_section'].includes(
                section.name,
              )
            ) {
              hasOrganizationSections.value = true
            } else if (
              ['contact_section', 'contact_details_section'].includes(
                section.name,
              )
            ) {
              hasContactSections.value = true
            }

            // Enhance status field with options
            if (field.fieldname === 'status') {
              return {
                ...field,
                fieldtype: 'Select',
                options: pipelineStatuses.value,
                prefix: getPipelineStatus(pipeline.doc.status)?.color || 'gray'
              }
            }

            return field
          }) || []
          return { ...column, fields }
        }) || []
        return { ...section, columns }
      }) || []
      return { ...tab, sections }
    })
    
    return transformedTabs
  },
})

const createPipeline = createResource({
  url: 'frappe.client.insert',
})

async function createNewPipeline() {
  console.log('Creating pipeline with final doc:', pipeline.doc)
  
  // Ensure pipeline_name is set
  if (!pipeline.doc.pipeline_name) {
    // Try to create pipeline_name from available fields
    if (pipeline.doc.first_name || pipeline.doc.last_name) {
      pipeline.doc.pipeline_name = [pipeline.doc.first_name, pipeline.doc.last_name]
        .filter(Boolean)
        .join(' ')
    } else if (pipeline.doc.organization) {
      pipeline.doc.pipeline_name = pipeline.doc.organization
    } else {
      pipeline.doc.pipeline_name = 'New Pipeline'
    }
  }
  
  if (pipeline.doc.website && !pipeline.doc.website.startsWith('http')) {
    pipeline.doc.website = 'https://' + pipeline.doc.website
  }

  // Handle existing contact/organization logic
  if (chooseExistingContact.value) {
    pipeline.doc['first_name'] = null
    pipeline.doc['last_name'] = null
    pipeline.doc['email'] = null
    pipeline.doc['mobile_no'] = null
  } else {
    pipeline.doc['contact'] = null
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
        
        // Check for pipeline_name OR first_name as mandatory
        if (!pipeline.doc.pipeline_name && !pipeline.doc.first_name) {
          error.value = __('Pipeline Name or First Name is mandatory')
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
        console.log('Pipeline created successfully:', data)
        capture('pipeline_created')
        isPipelineCreating.value = false
        show.value = false
        router.push({ name: 'Pipeline', params: { pipelineId: data.name } })
        updateOnboardingStep('create_first_pipeline', true, false, () => {
          localStorage.setItem('firstPipeline' + user, data.name)
        })
      },
      onError(err) {
        console.error('Error creating pipeline:', err)
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
  // Initialize pipeline document with defaults
  pipeline.doc = { 
    no_of_employees: '1-10',
    ...props.defaults 
  }

  if (!pipeline.doc?.pipeline_owner) {
    pipeline.doc.pipeline_owner = getUser().name
  }
  if (!pipeline.doc?.status && pipelineStatuses.value[0]?.value) {
    pipeline.doc.status = pipelineStatuses.value[0].value
  }

  // Set default pipeline_type if not already set
  if (!pipeline.doc?.pipeline_type) {
    pipeline.doc.pipeline_type = 'Default'
  }
  
  console.log('Pipeline modal mounted with initial doc:', pipeline.doc)
})
</script>
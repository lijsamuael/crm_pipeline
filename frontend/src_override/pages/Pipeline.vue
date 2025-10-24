<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template v-if="!errorTitle" #right-header>
      <CustomActions
        v-if="document._actions?.length"
        :actions="document._actions"
      />
      <CustomActions
        v-if="document.actions?.length"
        :actions="document.actions"
      />
      <AssignTo v-model="assignees.data" doctype="CRM Pipeline" :docname="pipelineId" />
      
      <!-- Change Status Button -->
      <Dropdown
        :options="statusOptions"
        placement="right"
      >
        <template #default="{ open }">
          <Button
            :label="__('Change Status')"
            :iconRight="open ? 'chevron-up' : 'chevron-down'"
            variant="outline"
          >
            <template #prefix>
              <IndicatorIcon :class="getPipelineStatus(doc.status).color" />
            </template>
          </Button>
        </template>
      </Dropdown>

      <Button
        :label="__('Convert to Deal')"
        variant="solid"
        @click="showConvertToDealModal = true"
      />

      <!-- Save Button (shown when there are changes) -->
      <Button
        v-if="hasChanges"
        :label="__('Save')"
        variant="solid"
        theme="green"
        @click="saveAllChanges"
        :loading="document.save.loading"
      />
    </template>
  </LayoutHeader>
  <div v-if="doc.name" class="flex h-full overflow-hidden">
    <Tabs as="div" v-model="tabIndex" :tabs="tabs">
      <template #tab-panel>
        <!-- Activities Tab -->
        <Activities
          v-if="currentTab?.name === 'Activity'"
          ref="activities"
          doctype="CRM Pipeline"
          :docname="pipelineId"
          :tabs="tabs"
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          @beforeSave="saveChanges"
          @afterSave="reloadAssignees"
        />

        <!-- Deal Tagging Tab -->
        <div v-else-if="currentTab?.name === 'DealTagging'" class="p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ __('Deal Tagging') }}</h3>
            <Button
              :label="__('Add New Deal')"
              variant="solid"
              icon="plus"
              @click="showAddDealModal = true"
            />
          </div>
          
          <!-- Add Deal Modal -->
          <Dialog v-model="showAddDealModal" :options="{ title: editingDeal ? __('Edit Deal') : __('Add New Deal'), size: '3xl' }">
            <template #body>
              <div class="p-4">
                <FieldLayout 
                  v-if="dealTabs.data" 
                  :tabs="dealTabs.data" 
                  :data="newDeal.doc" 
                  doctype="CRM Pipeline Items"
                />
                <div class="mt-4 flex justify-end gap-2">
                  <Button
                    :label="__('Cancel')"
                    variant="outline"
                    @click="cancelAddDeal"
                  />
                  <Button
                    :label="editingDeal ? __('Update Deal') : __('Save Deal')"
                    variant="solid"
                    theme="green"
                    :loading="isAddingDeal"
                    @click="saveDeal"
                  />
                </div>
              </div>
            </template>
          </Dialog>
          
          <div class="border rounded-lg overflow-hidden border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <table class="w-full">
              <thead class="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Deal Name') }}</th>
                  <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Deal Owner') }}</th>
                  <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Deal Value') }}</th>
                  <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Probability') }}</th>
                  <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Actions') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 dark:divide-gray-600">
                <tr 
                  v-for="deal in childDeals" 
                  :key="deal.name" 
                  class="hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  <td class="px-4 py-3 text-gray-900 dark:text-gray-100">
                    {{ deal.deal }}
                  </td>
                  <td class="px-4 py-3 text-gray-900 dark:text-gray-100">
                    {{ deal.deal_owner }}
                  </td>
                  <td class="px-4 py-3 text-gray-900 dark:text-gray-100">
                    {{ formatCurrency(deal.deal_value) }}
                  </td>
                  <td class="px-4 py-3 text-gray-900 dark:text-gray-100">
                    {{ deal.probability }}%
                  </td>
                  <td class="px-4 py-3">
                    <div class="flex gap-2">
                      <!-- <Button
                        :label="__('Edit')"
                        variant="ghost"
                        icon="edit"
                        @click="editDeal(deal)"
                      /> -->
                      <Button
                        :label="__('Delete')"
                        variant="subtle"
                        theme="red"
                        icon="trash-2"
                        @click="deleteDeal(deal.name)"
                      />
                    </div>
                  </td>
                </tr>
                <tr v-if="childDeals.length === 0">
                  <td colspan="6" class="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                    {{ __('No deals tagged to this pipeline.') }}
                    <Button
                      :label="__('Add your first deal')"
                      variant="ghost"
                      class="mt-2"
                      @click="showAddDealModal = true"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Logs Tab -->
        <div v-else-if="currentTab?.name === 'Logs'" class="p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ __('Status Logs') }}</h3>
          </div>
          
          <div class="border rounded-lg overflow-hidden border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <table class="w-full">
              <thead class="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('From Status') }}</th>
                  <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('To Status') }}</th>
                  <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('From Date') }}</th>
                  <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('To Date') }}</th>
                  <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Duration') }}</th>
                  <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Actions') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 dark:divide-gray-600">
                <tr v-for="(log, index) in localLogs" :key="index" class="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td class="px-4 py-3 text-gray-900 dark:text-gray-100">
                    {{ log.from_status }}
                  </td>
                  <td class="px-4 py-3 text-gray-900 dark:text-gray-100">
                    {{ log.to_status || 'Current' }}
                  </td>
                  <td class="px-4 py-3 text-gray-900 dark:text-gray-100">
                    {{ formatDate(log.from_date) }}
                  </td>
                  <td class="px-4 py-3 text-gray-900 dark:text-gray-100">
                    {{ log.to_date ? formatDate(log.to_date) : 'Ongoing' }}
                  </td>
                  <td class="px-4 py-3 text-gray-900 dark:text-gray-100">
                    {{ log.duration }}
                  </td>
                  <td class="px-4 py-3">
                    <Button
                      :label="__('Delete')"
                      variant="subtle"
                      theme="red"
                      icon="trash-2"
                      @click="removeLogRow(index)"
                    />
                  </td>
                </tr>
                <tr v-if="localLogs.length === 0">
                  <td colspan="6" class="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                    {{ __('No status logs available. Status changes will appear here automatically.') }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Default Activities for other tabs -->
        <Activities
          v-else
          ref="activities"
          doctype="CRM Pipeline"
          :docname="pipelineId"
          :tabs="tabs"
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          @beforeSave="saveChanges"
          @afterSave="reloadAssignees"
        />
      </template>
    </Tabs>
    <Resizer class="flex flex-col justify-between border-l border-gray-200 dark:border-gray-700" side="right">
      <div
        class="flex h-10.5 cursor-copy items-center border-b border-gray-200 dark:border-gray-700 px-5 py-2.5 text-lg font-medium text-gray-900 dark:text-gray-100"
        @click="copyToClipboard(pipelineId)"
      >
        {{ __(pipelineId) }}
      </div>
      <FileUploader
        @success="(file) => updateField('image', file.file_url)"
        :validateFile="validateIsImageFile"
      >
        <template #default="{ openFileSelector, error }">
          <div class="flex items-center justify-start gap-5 border-b border-gray-200 dark:border-gray-700 p-5">
            <div class="group relative size-12">
              <Avatar
                size="3xl"
                class="size-12"
                :label="title"
                :image="doc.image"
              />
              <component
                :is="doc.image ? Dropdown : 'div'"
                v-bind="
                  doc.image
                    ? {
                        options: [
                          {
                            icon: 'upload',
                            label: doc.image
                              ? __('Change image')
                              : __('Upload image'),
                            onClick: openFileSelector,
                          },
                          {
                            icon: 'trash-2',
                            label: __('Remove image'),
                            onClick: () => updateField('image', ''),
                          },
                        ],
                      }
                    : { onClick: openFileSelector }
                "
                class="!absolute bottom-0 left-0 right-0"
              >
                <div
                  class="z-1 absolute bottom-0.5 left-0 right-0.5 flex h-9 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 dark:bg-white dark:bg-opacity-20 pt-3 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                  style="
                    -webkit-clip-path: inset(12px 0 0 0);
                    clip-path: inset(12px 0 0 0);
                  "
                >
                  <CameraIcon class="size-4 cursor-pointer text-white dark:text-gray-100" />
                </div>
              </component>
            </div>
            <div class="flex flex-col gap-2.5 truncate">
              <Tooltip :text="doc.pipeline_name || __('Set name')">
                <div class="truncate text-2xl font-medium text-gray-900 dark:text-gray-100">
                  {{ title }}
                </div>
              </Tooltip>
              <div class="flex gap-1.5">
                <Button
                  v-if="callEnabled"
                  :tooltip="__('Make a call')"
                  :icon="PhoneIcon"
                  @click="
                    () =>
                      doc.mobile_no
                        ? makeCall(doc.mobile_no)
                        : toast.error(__('No phone number set'))
                  "
                />

                <Button
                  :tooltip="__('Send an email')"
                  :icon="Email2Icon"
                  @click="
                    doc.email ? openEmailBox() : toast.error(__('No email set'))
                  "
                />
                <Button
                  :tooltip="__('Go to website')"
                  :icon="LinkIcon"
                  @click="
                    doc.website
                      ? openWebsite(doc.website)
                      : toast.error(__('No website set'))
                  "
                />

                <Button
                  :tooltip="__('Attach a file')"
                  :icon="AttachmentIcon"
                  @click="showFilesUploader = true"
                />

                <Button
                  :tooltip="__('Delete')"
                  variant="subtle"
                  theme="red"
                  icon="trash-2"
                  @click="deletePipeline"
                />
              </div>
              <ErrorMessage :message="__(error)" />
            </div>
          </div>
        </template>
      </FileUploader>
      <SLASection
        v-if="doc.sla_status"
        v-model="doc"
        @updateField="updateField"
      />
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <SidePanelLayout
          :sections="sections.data"
          doctype="CRM Pipeline"
          :docname="pipelineId"
          @reload="sections.reload"
          @afterFieldChange="reloadAssignees"
        />
      </div>
    </Resizer>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <ConvertPipelineToDealModal
    v-if="showConvertToDealModal"
    v-model="showConvertToDealModal"
    :pipeline="doc"
  />
  <FilesUploader
    v-model="showFilesUploader"
    doctype="CRM Pipeline"
    :docname="pipelineId"
    @after="
      () => {
        activities?.all_activities?.reload()
        changeTabTo('attachments')
      }
    "
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'CRM Pipeline'"
    :docname="pipelineId"
    name="Pipelines"
  />
</template>

<script setup>
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import Icon from '@/components/Icon.vue'
import Resizer from '@/components/Resizer.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignTo from '@/components/AssignTo.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import ConvertPipelineToDealModal from '@/components/Modals/ConvertPipelineToDealModal.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import {
  openWebsite,
  setupCustomizations,
  copyToClipboard,
  validateIsImageFile,
} from '@/utils'
import { getView } from '@/utils/view'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { statusesStore } from '@/stores/statuses'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import { whatsappEnabled, callEnabled } from '@/composables/settings'
import {
  createResource,
  FileUploader,
  Dropdown,
  Tooltip,
  Avatar,
  Tabs,
  Breadcrumbs,
  call,
  usePageMeta,
  toast,
  Input,
  Badge,
  Dialog,
} from 'frappe-ui'
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const { brand } = getSettings()
const { $dialog, $socket, makeCall } = globalStore()
const { statusOptions: getStatusOptions, getPipelineStatus } = statusesStore()
const { doctypeMeta } = getMeta('CRM Pipeline')

const route = useRoute()
const router = useRouter()

const props = defineProps({
  pipelineId: {
    type: String,
    required: true,
  },
})

const reload = ref(false)
const activities = ref(null)
const errorTitle = ref('')
const errorMessage = ref('')
const showDeleteLinkedDocModal = ref(false)
const showConvertToDealModal = ref(false)
const showFilesUploader = ref(false)
const showAddDealModal = ref(false)
const isAddingDeal = ref(false)
const editingDeal = ref(null)

// Local state for logs
const localLogs = ref([])
const hasChanges = ref(false)

const { triggerOnChange, assignees, document, scripts, error } = useDocument(
  'CRM Pipeline',
  props.pipelineId,
)

const doc = computed(() => document.doc || {})

// Get deals from child table - FIXED: Check for deals child table
const childDeals = computed(() => {
  return doc.value.deals || []
})

// Resource for deal field layout
const dealTabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Pipeline Items'],
  params: { 
    doctype: 'CRM Pipeline Items', 
    type: 'Quick Entry'
  },
  auto: false,
})

// New deal document
const { document: newDeal } = useDocument('CRM Pipeline Items')

// Watch for document changes to initialize local state
watch(doc, (newDoc) => {
  if (newDoc) {
    localLogs.value = newDoc.logs ? JSON.parse(JSON.stringify(newDoc.logs)) : []
    hasChanges.value = false
  }
}, { immediate: true, deep: true })

// Watch for modal opening to reset form
watch(showAddDealModal, (show) => {
  if (show && !editingDeal.value) {
    // Reset for new deal
    newDeal.doc = {}
    // Load the custom field layout
    dealTabs.reload()
  }
})

// Watch for any changes in local state
watch([localLogs], ([newLogs], [oldLogs]) => {
  checkForChanges()
}, { deep: true })

// Status options for dropdown
const statusOptions = computed(() => {
  return getStatusOptions('pipeline').map(status => ({
    ...status,
    onClick: () => changePipelineStatus(status.value)
  }))
})

// Current active tab
const currentTab = computed(() => tabs.value[tabIndex.value])

// Tabs configuration with new tabs
const tabs = computed(() => {
  let tabOptions = [
    {
      name: 'Activity',
      label: __('Activity'),
      icon: ActivityIcon,
    },
    {
      name: 'DealTagging',
      label: __('Deal Tagging'),
      icon: DetailsIcon,
    },
    {
      name: 'Logs',
      label: __('Status Logs'),
      icon: ActivityIcon,
    },
    {
      name: 'Comments',
      label: __('Comments'),
      icon: CommentIcon,
    },
    {
      name: 'Data',
      label: __('Data'),
      icon: DetailsIcon,
    },
    {
      name: 'Tasks',
      label: __('Tasks'),
      icon: TaskIcon,
    },
    {
      name: 'Notes',
      label: __('Notes'),
      icon: NoteIcon,
    },
    {
      name: 'Attachments',
      label: __('Attachments'),
      icon: AttachmentIcon,
    },
    {
      name: 'WhatsApp',
      label: __('WhatsApp'),
      icon: WhatsAppIcon,
      condition: () => whatsappEnabled.value,
    },
  ]
  return tabOptions.filter((tab) => (tab.condition ? tab.condition() : true))
})

// Check if there are any changes
function checkForChanges() {
  const originalLogs = doc.value.logs ? JSON.parse(JSON.stringify(doc.value.logs)) : []
  const logsChanged = JSON.stringify(localLogs.value) !== JSON.stringify(originalLogs)
  
  hasChanges.value = logsChanged
}

// Save deal function
// Save deal function
async function saveDeal() {
  try {
    isAddingDeal.value = true
    
    // Validate required fields
    if (!newDeal.doc.deal) {
      toast.error(__('Deal Name is required'))
      return
    }

    console.log('Sending deal data:', newDeal.doc)

    // Prepare deal data with all required fields
    const dealData = {
      deal: newDeal.doc.deal,
      deal_owner: newDeal.doc.deal_owner,
      deal_value: newDeal.doc.deal_value,
      probability: newDeal.doc.probability,
      expected_deal_value: newDeal.doc.expected_deal_value,
      // Add any other fields from your form
      ...newDeal.doc
    }

    // Remove parent fields as they're not needed in the API
    delete dealData.parent
    delete dealData.parenttype
    delete dealData.parentfield

    console.log('Final deal data to send:', dealData)

    // Call the link_deal_to_pipeline API
    const result = await call('crm_pipeline.api.link_deal_to_pipeline', 
      {
        pipeline: props.pipelineId,
        deal_data: dealData
      }
    )

    console.log('Link deal response:', result)

    if (result && result.success) {
      toast.success(__('Deal added successfully'))
      
      // Close modal and reset
      showAddDealModal.value = false
      editingDeal.value = null
      newDeal.doc = {}
      
      // Reload the pipeline document to refresh the child table
      document.reload()
    } else {
      throw new Error(result?.error || __('Failed to add deal'))
    }
    
  } catch (error) {
    console.error('Error saving deal:', error)
    toast.error(__('Failed to save deal: {0}', [error.message]))
  } finally {
    isAddingDeal.value = false
  }
}


// Cancel adding/editing deal
function cancelAddDeal() {
  showAddDealModal.value = false
  editingDeal.value = null
  newDeal.doc = {}
}

// Delete deal function
async function deleteDeal(dealName) {
  try {
    
      // Call API to delete the deal from child table
      const result = await call('crm_pipeline.api.unlink_deal_from_pipeline', {
        pipeline: props.pipelineId,
        deal_name: dealName
      })

      if (result && result.success) {
        toast.success(__('Deal deleted successfully'))
        
        // Reload the pipeline document to refresh the child table
        document.reload()
      } else {
        throw new Error(result?.error || __('Failed to delete deal'))
      }
  } catch (error) {
    console.error('Error deleting deal:', error)
    toast.error(__('Failed to delete deal: {0}', [error.message]))
  }
}

// Format currency
function formatCurrency(value) {
  if (!value) return '0.00'
  return parseFloat(value).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}



// Logs Functions
function removeLogRow(index) {
  localLogs.value.splice(index, 1)
}

// Status Change Function
async function changePipelineStatus(newStatus) {
  try {
    await call('crm_pipeline.api.update_pipeline_status', {
      pipeline_name: props.pipelineId,
      new_status: newStatus
    })
    toast.success(__('Status updated successfully'))
    document.reload()
  } catch (error) {
    toast.error(__('Failed to update status: {0}', [error.message]))
  }
}

// Save all changes
async function saveAllChanges() {
  try {
    // Update logs
    doc.value.logs = localLogs.value
    
    // Save the document
    await document.save.submit()
    
    hasChanges.value = false
    toast.success(__('Changes saved successfully'))
  } catch (error) {
    toast.error(__('Failed to save changes: {0}', [error.message]))
  }
}

// Existing functions
const { tabIndex, changeTabTo } = useActiveTabManager(tabs, 'lastPipelineTab')

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'CRM Pipeline'],
  params: { doctype: 'CRM Pipeline' },
  auto: true,
})

const breadcrumbs = computed(() => {
  let items = [{ label: __('Pipelines'), route: { name: 'Pipelines' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'CRM Pipeline')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Pipelines',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: { name: 'Pipeline', params: { pipelineId: props.pipelineId } },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta['CRM Pipeline']?.title_field || 'name'
  return doc.value?.[t] || props.pipelineId
})

usePageMeta(() => {
  return { title: title.value, icon: brand.favicon }
})

watch(error, (err) => {
  if (err) {
    errorTitle.value = __(
      err.exc_type == 'DoesNotExistError'
        ? 'Document not found'
        : 'Error occurred',
    )
    errorMessage.value = __(err.messages?.[0] || 'An error occurred')
  } else {
    errorTitle.value = ''
    errorMessage.value = ''
  }
})

watch(
  () => document.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        toast,
        updateField,
        createToast: toast.create,
        deleteDoc: deletePipeline,
        call,
      })
      document._actions = s.actions || []
      document._statuses = s.statuses || []
    }
  },
  { once: true },
)

async function triggerStatusChange(value) {
  await triggerOnChange('status', value)
  document.save.submit()
}

function updateField(name, value) {
  value = Array.isArray(name) ? '' : value
  let oldValues = Array.isArray(name) ? {} : doc.value[name]

  if (Array.isArray(name)) {
    name.forEach((field) => (doc.value[field] = value))
  } else {
    doc.value[name] = value
  }

  document.save.submit(null, {
    onSuccess: () => (reload.value = true),
    onError: (err) => {
      if (Array.isArray(name)) {
        name.forEach((field) => (doc.value[field] = oldValues[field]))
      } else {
        doc.value[name] = oldValues
      }
      toast.error(err.messages?.[0] || __('Error updating field'))
    },
  })
}

function deletePipeline() {
  showDeleteLinkedDocModal.value = true
}

function openEmailBox() {
  let currentTab = tabs.value[tabIndex.value]
  if (!['Emails', 'Comments', 'Activities'].includes(currentTab.name)) {
    activities.value.changeTabTo('emails')
  }
  nextTick(() => (activities.value.emailBox.show = true))
}

function saveChanges(data) {
  document.save.submit(null, {
    onSuccess: () => reloadAssignees(data),
  })
}

function reloadAssignees(data) {
  if (data?.hasOwnProperty('pipeline_owner')) {
    assignees.reload()
  }
}

function formatDate(dateString) {
  if (!dateString) return ''
  
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return dateString
    
    // Use browser's locale for formatting
    return date.toLocaleString()
  } catch (error) {
    return dateString
  }
}
</script>
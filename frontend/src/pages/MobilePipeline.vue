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
      <!-- <AssignTo v-model="assignees.data" doctype="CRM Pipeline" :docname="pipelineId" /> -->

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
    <Tabs as="div" v-model="tabIndex" :tabs="filteredTabs">
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

        <!-- Deals Tab -->
        <div v-else-if="currentTab?.name === 'Deals'" class="p-5">
          <!-- Header with Title and Actions -->
          <div class="flex flex-col gap-4 mb-6">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ __('Deals') }}</h3>
              <Button
                :label="__('Add New Deal')"
                variant="solid"
                icon="plus"
                @click="showAddDealModal = true"
              />
            </div>
            
            <!-- Convert and Status Change Buttons -->
            <div class="flex flex-wrap gap-2">
              <Button
                v-if="doc.pipeline_type === 'Default'"
                :label="__('Convert to Deal')"
                variant="solid"
                @click="showConvertToDealModal = true"
              />
              
              <Dropdown
                :options="statusOptions"
                placement="bottom-end"
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
            </div>
          </div>

          <!-- Deals Summary -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{{ __('Total Deals') }}</div>
              <div class="text-2xl font-bold text-gray-900 dark:text-gray-100">{{ dealsSummary.totalDeals }}</div>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{{ __('Total Value') }}</div>
              <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ formatCurrency(dealsSummary.totalValue) }}</div>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{{ __('Expected Sales') }}</div>
              <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ formatCurrency(dealsSummary.expectedSales) }}</div>
            </div>
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
          
          <!-- Scrollable Deals Table -->
          <div class="border rounded-lg overflow-hidden border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div class="overflow-x-auto">
              <table class="w-full min-w-max">
                <thead class="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <!-- Dynamic Columns based on API response -->
                    <th 
                      v-for="column in dealGridColumns" 
                      :key="column.fieldname"
                      class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap"
                    >
                      {{ column.label }}
                    </th>
                    <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">{{ __('Actions') }}</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-600">
                  <tr 
                    v-for="deal in childDeals" 
                    :key="deal.name" 
                    class="hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    <!-- Dynamic Deal Data -->
                    <td 
                      v-for="column in dealGridColumns" 
                      :key="column.fieldname"
                      class="px-4 py-3 text-gray-900 dark:text-gray-100 whitespace-nowrap"
                    >
                      <template v-if="column.fieldtype === 'Float'">
                        {{ formatCurrency(deal[column.fieldname]) }}
                      </template>
                      <template v-else-if="column.fieldtype === 'Percent'">
                        {{ deal[column.fieldname] }}%
                      </template>
                      <template v-else>
                        {{ deal[column.fieldname] }}
                      </template>
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap">
                      <div class="flex gap-2">
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
                    <td :colspan="dealGridColumns.length + 1" class="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
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
        </div>

        <!-- Pipelines Tab -->
        <div v-else-if="currentTab?.name === 'Pipelines'" class="p-5">
          <!-- Header with Title and Actions -->
          <div class="flex flex-col gap-4 mb-6">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ __('Child Pipelines') }}</h3>
              <Button
                :label="__('Add New Pipeline')"
                variant="solid"
                icon="plus"
                @click="showAddPipelineModal = true"
              />
            </div>
            
            <!-- Convert and Status Change Buttons -->
            <div class="flex flex-wrap gap-2">
              <Button
                v-if="doc.pipeline_type === 'Default'"
                :label="__('Convert to Deal')"
                variant="solid"
                @click="showConvertToDealModal = true"
              />
              
              <Dropdown
                :options="statusOptions"
                placement="bottom-end"
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
            </div>
          </div>

          <!-- Pipelines Summary -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{{ __('Total Pipelines') }}</div>
              <div class="text-2xl font-bold text-gray-900 dark:text-gray-100">{{ pipelinesSummary.totalPipelines }}</div>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{{ __('Total Deals') }}</div>
              <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ pipelinesSummary.totalDeals }}</div>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{{ __('Total Sales') }}</div>
              <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ formatCurrency(pipelinesSummary.totalSales) }}</div>
            </div>
          </div>
          
          <!-- Add Pipeline Modal -->
          <Dialog v-model="showAddPipelineModal" :options="{ title: editingPipeline ? __('Edit Pipeline') : __('Add New Pipeline'), size: '3xl' }">
            <template #body>
              <div class="p-4">
                <FieldLayout 
                  v-if="pipelineTabs.data" 
                  :tabs="pipelineTabs.data" 
                  :data="newPipeline.doc" 
                  doctype="CRM Master Pipeline Child"
                />
                <div class="mt-4 flex justify-end gap-2">
                  <Button
                    :label="__('Cancel')"
                    variant="outline"
                    @click="cancelAddPipeline"
                  />
                  <Button
                    :label="editingPipeline ? __('Update Pipeline') : __('Save Pipeline')"
                    variant="solid"
                    theme="green"
                    :loading="isAddingPipeline"
                    @click="savePipeline"
                  />
                </div>
              </div>
            </template>
          </Dialog>
          
          <!-- Scrollable Pipelines Table -->
          <div class="border rounded-lg overflow-hidden border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div class="overflow-x-auto">
              <table class="w-full min-w-max">
                <thead class="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <!-- Dynamic Columns based on API response -->
                    <th 
                      v-for="column in pipelineGridColumns" 
                      :key="column.fieldname"
                      class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap"
                    >
                      {{ column.label }}
                    </th>
                    <!-- Static columns for total deals, total value, and actions -->
                    <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">{{ __('Total Deals') }}</th>
                    <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">{{ __('Total Value') }}</th>
                    <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">{{ __('Actions') }}</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-600">
                  <tr 
                    v-for="pipeline in childPipelinesWithDetails" 
                    :key="pipeline.name" 
                    class="hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    <!-- Dynamic Pipeline Data -->
                    <td 
                      v-for="column in pipelineGridColumns" 
                      :key="column.fieldname"
                      class="px-4 py-3 text-gray-900 dark:text-gray-100 whitespace-nowrap"
                    >
                      <template v-if="column.fieldname === 'status'">
                        <Badge :variant="getPipelineStatus(pipeline[column.fieldname]).variant" :theme="getPipelineStatus(pipeline[column.fieldname]).theme">
                          {{ pipeline[column.fieldname] }}
                        </Badge>
                      </template>
                      <template v-else-if="column.fieldtype === 'Float'">
                        {{ formatCurrency(pipeline[column.fieldname]) }}
                      </template>
                      <template v-else-if="column.fieldtype === 'Percent'">
                        {{ pipeline[column.fieldname] }}%
                      </template>
                      <template v-else>
                        {{ pipeline[column.fieldname] }}
                      </template>
                    </td>
                    <!-- Static columns data -->
                    <td class="px-4 py-3 text-gray-900 dark:text-gray-100 whitespace-nowrap">
                      {{ pipeline.total_deals || 0 }}
                    </td>
                    <td class="px-4 py-3 text-gray-900 dark:text-gray-100 whitespace-nowrap">
                      {{ formatCurrency(pipeline.total_value || 0) }}
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap">
                      <div class="flex gap-2">
                        <Button
                          :label="__('Delete')"
                          variant="subtle"
                          theme="red"
                          icon="trash-2"
                          @click="deletePipeline(pipeline.name)"
                        />
                      </div>
                    </td>
                  </tr>
                  <tr v-if="childPipelines.length === 0">
                    <td :colspan="pipelineGridColumns.length + 3" class="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                      {{ __('No child pipelines linked to this master pipeline.') }}
                      <Button
                        :label="__('Add your first pipeline')"
                        variant="ghost"
                        class="mt-2"
                        @click="showAddPipelineModal = true"
                      />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Status Tab -->
        <div v-else-if="currentTab?.name === 'Status'" class="p-5">
          <!-- Header with Title and Actions -->
          <div class="flex flex-col gap-4 mb-6">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ __('Status') }}</h3>
            </div>
            
            <!-- Convert and Status Change Buttons -->
            <div class="flex flex-wrap gap-2">
              <Button
                v-if="doc.pipeline_type === 'Default'"
                :label="__('Convert to Deal')"
                variant="solid"
                @click="showConvertToDealModal = true"
              />
              
              <Dropdown
                :options="statusOptions"
                placement="bottom-end"
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
            </div>
          </div>
          
          <!-- Scrollable Status Table -->
          <div class="border rounded-lg overflow-hidden border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div class="overflow-x-auto">
              <table class="w-full min-w-max">
                <thead class="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">{{ __('From Status') }}</th>
                    <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">{{ __('To Status') }}</th>
                    <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">{{ __('From Date') }}</th>
                    <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">{{ __('To Date') }}</th>
                    <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">{{ __('Duration') }}</th>
                    <th class="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">{{ __('Actions') }}</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-600">
                  <tr v-for="(log, index) in localLogs" :key="index" class="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td class="px-4 py-3 text-gray-900 dark:text-gray-100 whitespace-nowrap">
                      {{ log.from_status }}
                    </td>
                    <td class="px-4 py-3 text-gray-900 dark:text-gray-100 whitespace-nowrap">
                      {{ log.to_status || 'Current' }}
                    </td>
                    <td class="px-4 py-3 text-gray-900 dark:text-gray-100 whitespace-nowrap">
                      {{ formatDate(log.from_date) }}
                    </td>
                    <td class="px-4 py-3 text-gray-900 dark:text-gray-100 whitespace-nowrap">
                      {{ log.to_date ? formatDate(log.to_date) : 'Ongoing' }}
                    </td>
                    <td class="px-4 py-3 text-gray-900 dark:text-gray-100 whitespace-nowrap">
                      {{ log.duration }}
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap">
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
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />

  <!-- Convert to Deal Modal -->
  <Dialog
    v-model="showConvertToDealModal"
    :options="{
      title: __('Convert to Deal'),
      size: 'xl',
      actions: [
        {
          label: __('Convert'),
          variant: 'solid',
          onClick: convertToDeal,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="mb-4 flex items-center gap-2 text-ink-gray-5">
        <OrganizationsIcon class="h-4 w-4" />
        <label class="block text-base">{{ __('Organization') }}</label>
      </div>
      <div class="ml-6">
        <div class="flex items-center justify-between text-base">
          <div>{{ __('Choose Existing') }}</div>
          <Switch v-model="existingOrganizationChecked" />
        </div>
        <Link
          v-if="existingOrganizationChecked"
          class="form-control mt-2.5"
          variant="outline"
          size="md"
          :value="existingOrganization"
          doctype="CRM Organization"
          @change="(data) => (existingOrganization = data)"
        />
        <div v-else class="mt-2.5 text-base">
          {{
            __(
              'New organization will be created based on the data in details section',
            )
          }}
        </div>
      </div>

      <div class="mb-4 mt-6 flex items-center gap-2 text-ink-gray-5">
        <ContactsIcon class="h-4 w-4" />
        <label class="block text-base">{{ __('Contact') }}</label>
      </div>
      <div class="ml-6">
        <div class="flex items-center justify-between text-base">
          <div>{{ __('Choose Existing') }}</div>
          <Switch v-model="existingContactChecked" />
        </div>
        <Link
          v-if="existingContactChecked"
          class="form-control mt-2.5"
          variant="outline"
          size="md"
          :value="existingContact"
          doctype="Contact"
          @change="(data) => (existingContact = data)"
        />
        <div v-else class="mt-2.5 text-base">
          {{ __("New contact will be created based on the person's details") }}
        </div>
      </div>
    </template>
  </Dialog>

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
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignTo from '@/components/AssignTo.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import CustomActions from '@/components/CustomActions.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import {
  setupCustomizations,
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
  Dropdown,
  Tabs,
  Breadcrumbs,
  call,
  usePageMeta,
  toast,
  Badge,
  Dialog,
  Switch,
  Link,
} from 'frappe-ui'
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const { brand } = getSettings()
const { $dialog, $socket } = globalStore()
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

// Pipeline modal state
const showAddPipelineModal = ref(false)
const isAddingPipeline = ref(false)
const editingPipeline = ref(null)

// Convert to deal modal state
const existingContactChecked = ref(false)
const existingOrganizationChecked = ref(false)
const existingContact = ref('')
const existingOrganization = ref('')

// Local state for logs
const localLogs = ref([])
const hasChanges = ref(false)

// Reactive variable for child pipelines with details
const childPipelinesWithDetailsData = ref([])

// Deal grid layout data
const dealGridLayout = ref({
  data: null
})

// Pipeline grid layout data
const pipelineGridLayout = ref({
  data: null
})

const { triggerOnChange, assignees, document, scripts, error } = useDocument(
  'CRM Pipeline',
  props.pipelineId,
)

const doc = computed(() => document.doc || {})

// Get deals from child table
const childDeals = computed(() => {
  return doc.value.deals || []
})

// Get child pipelines from sub_pipelines child table
const childPipelines = computed(() => {
  return doc.value.sub_pipelines || []
})

// Get child pipelines with deal details
const childPipelinesWithDetails = computed(() => {
  return childPipelinesWithDetailsData.value.length > 0 
    ? childPipelinesWithDetailsData.value 
    : childPipelines.value.map(pipeline => ({
        ...pipeline,
        total_deals: 0,
        total_value: 0
      }))
})

// Dynamic deal grid columns based on API response
const dealGridColumns = computed(() => {
  if (dealGridLayout.value.data && dealGridLayout.value.data.columns) {
    return dealGridLayout.value.data.columns.filter(column => !column.hidden)
  }
  return [
    {
      fieldname: 'deal',
      label: 'Deal',
      fieldtype: 'Link',
      options: 'CRM Deal',
      width: null,
      read_only: 0,
      hidden: 0,
      reqd: 0
    },
    {
      fieldname: 'deal_owner',
      label: 'Deal Owner',
      fieldtype: 'Link',
      options: 'User',
      width: null,
      read_only: 0,
      hidden: 0,
      reqd: 0
    },
    {
      fieldname: 'deal_value',
      label: 'Deal Value',
      fieldtype: 'Float',
      options: null,
      width: null,
      read_only: 0,
      hidden: 0,
      reqd: 0
    }
  ]
})

// Dynamic pipeline grid columns based on API response
const pipelineGridColumns = computed(() => {
  if (pipelineGridLayout.value.data && pipelineGridLayout.value.data.columns) {
    return pipelineGridLayout.value.data.columns.filter(column => !column.hidden)
  }
  return [
    {
      fieldname: 'pipeline_name',
      label: 'Pipeline Name',
      fieldtype: 'Data',
      width: null,
      read_only: 0,
      hidden: 0,
      reqd: 0
    },
    {
      fieldname: 'pipeline_owner',
      label: 'Pipeline Owner',
      fieldtype: 'Link',
      options: 'User',
      width: null,
      read_only: 0,
      hidden: 0,
      reqd: 0
    },
    {
      fieldname: 'status',
      label: 'Status',
      fieldtype: 'Select',
      width: null,
      read_only: 0,
      hidden: 0,
      reqd: 0
    }
  ]
})

// Deals summary calculations
const dealsSummary = computed(() => {
  const deals = childDeals.value
  const totalDeals = deals.length
  const totalValue = deals.reduce((sum, deal) => sum + (parseFloat(deal.deal_value) || 0), 0)
  const expectedSales = deals.reduce((sum, deal) => {
    const value = parseFloat(deal.deal_value) || 0
    const probability = parseFloat(deal.probability) || 0
    return sum + (value * (probability / 100))
  }, 0)
  
  return {
    totalDeals,
    totalValue,
    expectedSales
  }
})

// Pipelines summary calculations
const pipelinesSummary = computed(() => {
  const pipelines = childPipelinesWithDetails.value
  const totalPipelines = pipelines.length
  
  let totalDeals = 0
  let totalSales = 0
  
  pipelines.forEach(pipeline => {
    totalDeals += pipeline.total_deals || 0
    totalSales += parseFloat(pipeline.total_value) || 0
  })
  
  return {
    totalPipelines,
    totalDeals,
    totalSales
  }
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

// Resource for pipeline field layout
const pipelineTabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Master Pipeline Child'],
  params: { 
    doctype: 'CRM Master Pipeline Child', 
    type: 'Quick Entry'
  },
  auto: false,
})

// New deal document
const { document: newDeal } = useDocument('CRM Pipeline Items')

// New pipeline document
const { document: newPipeline } = useDocument('CRM Master Pipeline Child')

// Load deal grid layout
function loadDealGridLayout() {
  call('crm_pipeline.api.get_grid_layout', {
    doctype: "CRM Pipeline Items",
  })
    .then((r) => {
      dealGridLayout.value.data = r
    })
    .catch((e) => {
      console.error("Failed to load grid layout:", e)
      toast.error(e.message || __('Failed to load grid layout'))
    })
}

// Load pipeline grid layout
function loadPipelineGridLayout() {
  call('crm_pipeline.api.get_grid_layout', {
    doctype: "CRM Master Pipeline Child",
  })
    .then((r) => {
      pipelineGridLayout.value.data = r
    })
    .catch((e) => {
      console.error("Failed to load pipeline grid layout:", e)
      toast.error(e.message || __('Failed to load pipeline grid layout'))
    })
}

// Load child pipelines with deals data
async function loadChildPipelinesWithDeals() {
  try {
    const result = await call('crm_pipeline.api.get_child_pipelines_with_deals', {
      master_pipeline: props.pipelineId
    })
    
    if (result && result.success) {
      childPipelinesWithDetailsData.value = result.child_pipelines || []
    } else {
      childPipelinesWithDetailsData.value = []
    }
  } catch (error) {
    console.error('Error loading child pipelines with deals:', error)
    childPipelinesWithDetailsData.value = []
  }
}

// Watch for document changes
watch(doc, async (newDoc) => {
  if (newDoc) {
    localLogs.value = newDoc.logs ? JSON.parse(JSON.stringify(newDoc.logs)) : []
    hasChanges.value = false
    
    loadDealGridLayout()
    loadPipelineGridLayout()
    
    if (newDoc.pipeline_type === 'Master Pipeline') {
      await loadChildPipelinesWithDeals()
    }
  }
}, { immediate: true, deep: true })

// Watch for modal opening to reset form
watch(showAddDealModal, (show) => {
  if (show && !editingDeal.value) {
    newDeal.doc = {}
    dealTabs.reload()
  }
})

watch(showAddPipelineModal, (show) => {
  if (show && !editingPipeline.value) {
    newPipeline.doc = {}
    pipelineTabs.reload()
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
const currentTab = computed(() => filteredTabs.value[tabIndex.value])

// Tabs configuration
const tabs = computed(() => {
  let tabOptions = [
    {
      name: 'Activity',
      label: __('Activity'),
      icon: ActivityIcon,
    },
    {
      name: 'Deals',
      label: __('Deals'),
      icon: DetailsIcon,
      condition: () => doc.value.pipeline_type === 'Default'
    },
    {
      name: 'Pipelines',
      label: __('Pipelines'),
      icon: DetailsIcon,
      condition: () => doc.value.pipeline_type === 'Master Pipeline'
    },
    {
      name: 'Status',
      label: __('Status'),
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

// Filtered tabs based on conditions
const filteredTabs = computed(() => {
  return tabs.value.filter(tab => tab.condition ? tab.condition() : true)
})

// Check if there are any changes
function checkForChanges() {
  const originalLogs = doc.value.logs ? JSON.parse(JSON.stringify(doc.value.logs)) : []
  const logsChanged = JSON.stringify(localLogs.value) !== JSON.stringify(originalLogs)
  
  hasChanges.value = logsChanged
}

// Save deal function
async function saveDeal() {
  try {
    isAddingDeal.value = true
    
    if (!newDeal.doc.deal) {
      toast.error(__('Deal Name is required'))
      return
    }

    const dealData = {
      deal: newDeal.doc.deal,
      deal_owner: newDeal.doc.deal_owner,
      deal_value: newDeal.doc.deal_value,
      probability: newDeal.doc.probability,
      expected_deal_value: newDeal.doc.expected_deal_value,
      ...newDeal.doc
    }

    delete dealData.parent
    delete dealData.parenttype
    delete dealData.parentfield

    const result = await call('crm_pipeline.api.link_deal_to_pipeline', 
      {
        pipeline: props.pipelineId,
        deal_data: dealData
      }
    )

    if (result && result.success) {
      toast.success(__('Deal added successfully'))
      showAddDealModal.value = false
      editingDeal.value = null
      newDeal.doc = {}
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

// Save pipeline function
async function savePipeline() {
  try {
    isAddingPipeline.value = true
    
    if (!newPipeline.doc.pipeline_name) {
      toast.error(__('Pipeline Name is required'))
      return
    }

    const pipelineData = {
      pipeline_name: newPipeline.doc.pipeline_name,
      pipeline_owner: newPipeline.doc.pipeline_owner,
      status: newPipeline.doc.status || 'Active',
      ...newPipeline.doc
    }

    delete pipelineData.parent
    delete pipelineData.parenttype
    delete pipelineData.parentfield

    const result = await call('crm_pipeline.api.link_pipeline_to_master', 
      {
        pipeline: props.pipelineId,
        pipeline_data: pipelineData
      }
    )

    if (result && result.success) {
      toast.success(__('Pipeline added successfully'))
      showAddPipelineModal.value = false
      editingPipeline.value = null
      newPipeline.doc = {}
      document.reload()
      await loadChildPipelinesWithDeals()
    } else {
      throw new Error(result?.error || __('Failed to add pipeline'))
    }
    
  } catch (error) {
    console.error('Error saving pipeline:', error)
    toast.error(__('Failed to save pipeline: {0}', [error.message]))
  } finally {
    isAddingPipeline.value = false
  }
}

// Cancel adding/editing deal
function cancelAddDeal() {
  showAddDealModal.value = false
  editingDeal.value = null
  newDeal.doc = {}
}

// Cancel adding/editing pipeline
function cancelAddPipeline() {
  showAddPipelineModal.value = false
  editingPipeline.value = null
  newPipeline.doc = {}
}

// Delete deal function
async function deleteDeal(dealName) {
  try {
    const result = await call('crm_pipeline.api.unlink_deal_from_pipeline', {
      pipeline: props.pipelineId,
      deal_name: dealName
    })

    if (result && result.success) {
      toast.success(__('Deal deleted successfully'))
      document.reload()
    } else {
      throw new Error(result?.error || __('Failed to delete deal'))
    }
  } catch (error) {
    console.error('Error deleting deal:', error)
    toast.error(__('Failed to delete deal: {0}', [error.message]))
  }
}

// Delete pipeline function
async function deletePipeline(pipelineName) {
  try {
    const result = await call('crm_pipeline.api.unlink_pipeline_from_master', {
      pipeline: props.pipelineId,
      pipeline_name: pipelineName
    })

    if (result && result.success) {
      toast.success(__('Pipeline deleted successfully'))
      document.reload()
      await loadChildPipelinesWithDeals()
    } else {
      throw new Error(result?.error || __('Failed to delete pipeline'))
    }
  } catch (error) {
    console.error('Error deleting pipeline:', error)
    toast.error(__('Failed to delete pipeline: {0}', [error.message]))
  }
}

// Convert to Deal function
async function convertToDeal() {
  if (existingContactChecked.value && !existingContact.value) {
    toast.error(__('Please select an existing contact'))
    return
  }

  if (existingOrganizationChecked.value && !existingOrganization.value) {
    toast.error(__('Please select an existing organization'))
    return
  }

  if (!existingContactChecked.value && existingContact.value) {
    existingContact.value = ''
  }

  if (!existingOrganizationChecked.value && existingOrganization.value) {
    existingOrganization.value = ''
  }

  let deal = await call('crm.fcrm.doctype.crm_pipeline.crm_pipeline.convert_to_deal', {
    pipeline: props.pipelineId,
    deal: {},
    existing_contact: existingContact.value,
    existing_organization: existingOrganization.value,
  })
  if (deal) {
    showConvertToDealModal.value = false
    existingContactChecked.value = false
    existingOrganizationChecked.value = false
    existingContact.value = ''
    existingOrganization.value = ''
    router.push({ name: 'Deal', params: { dealId: deal } })
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
    doc.value.logs = localLogs.value
    await document.save.submit()
    hasChanges.value = false
    toast.success(__('Changes saved successfully'))
  } catch (error) {
    toast.error(__('Failed to save changes: {0}', [error.message]))
  }
}

// Existing functions
const { tabIndex, changeTabTo } = useActiveTabManager(tabs, 'lastPipelineTab')

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
        deleteDoc: deleteCurrentPipeline,
        call,
      })
      document._actions = s.actions || []
      document._statuses = s.statuses || []
    }
  },
  { once: true },
)

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

function deleteCurrentPipeline() {
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
    return date.toLocaleString()
  } catch (error) {
    return dateString
  }
}
</script>
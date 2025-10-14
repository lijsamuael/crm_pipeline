<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Pipelines" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="pipelinesListView?.customListActions"
        :actions="pipelinesListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="showPipelineModal = true"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="pipelines"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Pipeline"
    :options="{
      allowedViews: ['list', 'group_by', 'kanban'],
    }"
  />
  <KanbanView
    v-if="route.params.viewType == 'kanban'"
    v-model="pipelines"
    :options="{
      getRoute: (row) => ({
        name: 'Pipeline',
        params: { pipelineId: row.name },
        query: { view: route.query.view, viewType: route.params.viewType },
      }),
      onNewClick: (column) => onNewClick(column),
    }"
    @update="(data) => viewControls.updateKanbanSettings(data)"
    @loadMore="(columnName) => viewControls.loadMoreKanban(columnName)"
  >
    <template #title="{ titleField, itemName }">
      <div class="flex items-center gap-2">
        <div v-if="titleField === 'status'">
          <IndicatorIcon :class="getRow(itemName, titleField).color" />
        </div>
        <div
          v-else-if="
            titleField === 'organization' && getRow(itemName, titleField).label
          "
        >
          <Avatar
            class="flex items-center"
            :image="getRow(itemName, titleField).logo"
            :label="getRow(itemName, titleField).label"
            size="sm"
          />
        </div>
        <div
          v-else-if="
            titleField === 'pipeline_name' && getRow(itemName, titleField).label
          "
        >
          <Avatar
            class="flex items-center"
            :image="getRow(itemName, titleField).image"
            :label="getRow(itemName, titleField).image_label"
            size="sm"
          />
        </div>
        <div
          v-else-if="
            titleField === 'pipeline_owner' &&
            getRow(itemName, titleField).full_name
          "
        >
          <Avatar
            class="flex items-center"
            :image="getRow(itemName, titleField).user_image"
            :label="getRow(itemName, titleField).full_name"
            size="sm"
          />
        </div>
        <div v-else-if="titleField === 'mobile_no'">
          <PhoneIcon class="h-4 w-4" />
        </div>
        <div
          v-if="
            [
              'modified',
              'creation',
            ].includes(titleField)
          "
          class="truncate text-base"
        >
          <Tooltip :text="getRow(itemName, titleField).label">
            <div>{{ getRow(itemName, titleField).timeAgo }}</div>
          </Tooltip>
        </div>
        <div
          v-else-if="getRow(itemName, titleField).label"
          class="truncate text-base"
        >
          {{ getRow(itemName, titleField).label }}
        </div>
        <div class="text-ink-gray-4" v-else>{{ __('No Title') }}</div>
      </div>
    </template>
    <template #fields="{ fieldName, itemName }">
      <div
        v-if="getRow(itemName, fieldName).label"
        class="truncate flex items-center gap-2"
      >
        <div v-if="fieldName === 'status'">
          <IndicatorIcon :class="getRow(itemName, fieldName).color" />
        </div>
        <div
          v-else-if="
            fieldName === 'organization' && getRow(itemName, fieldName).label
          "
        >
          <Avatar
            class="flex items-center"
            :image="getRow(itemName, fieldName).logo"
            :label="getRow(itemName, fieldName).label"
            size="xs"
          />
        </div>
        <div v-else-if="fieldName === 'pipeline_name'">
          <Avatar
            v-if="getRow(itemName, fieldName).label"
            class="flex items-center"
            :image="getRow(itemName, fieldName).image"
            :label="getRow(itemName, fieldName).image_label"
            size="xs"
          />
        </div>
        <div v-else-if="fieldName === 'pipeline_owner'">
          <Avatar
            v-if="getRow(itemName, fieldName).full_name"
            class="flex items-center"
            :image="getRow(itemName, fieldName).user_image"
            :label="getRow(itemName, fieldName).full_name"
            size="xs"
          />
        </div>
        <div
          v-if="
            [
              'modified',
              'creation',
            ].includes(fieldName)
          "
          class="truncate text-base"
        >
          <Tooltip :text="getRow(itemName, fieldName).label">
            <div>{{ getRow(itemName, fieldName).timeAgo }}</div>
          </Tooltip>
        </div>
        <div v-else-if="fieldName === '_assign'" class="flex items-center">
          <MultipleAvatar
            :avatars="getRow(itemName, fieldName).label"
            size="xs"
          />
        </div>
        <div v-else class="truncate text-base">
          {{ getRow(itemName, fieldName).label }}
        </div>
      </div>
    </template>
    <template #actions="{ itemName }">
      <div class="flex gap-2 items-center justify-between">
        <div class="text-ink-gray-5 flex items-center gap-1.5">
          <EmailAtIcon class="h-4 w-4" />
          <span v-if="getRow(itemName, '_email_count').label">
            {{ getRow(itemName, '_email_count').label }}
          </span>
          <span class="text-3xl leading-[0]"> &middot; </span>
          <NoteIcon class="h-4 w-4" />
          <span v-if="getRow(itemName, '_note_count').label">
            {{ getRow(itemName, '_note_count').label }}
          </span>
          <span class="text-3xl leading-[0]"> &middot; </span>
          <TaskIcon class="h-4 w-4" />
          <span v-if="getRow(itemName, '_task_count').label">
            {{ getRow(itemName, '_task_count').label }}
          </span>
          <span class="text-3xl leading-[0]"> &middot; </span>
          <CommentIcon class="h-4 w-4" />
          <span v-if="getRow(itemName, '_comment_count').label">
            {{ getRow(itemName, '_comment_count').label }}
          </span>
        </div>
        <Dropdown
          class="flex items-center gap-2"
          :options="actions(itemName)"
          variant="ghost"
          @click.stop.prevent
        >
          <Button icon="plus" variant="ghost" />
        </Dropdown>
      </div>
    </template>
  </KanbanView>
  <PipelinesListView
    ref="pipelinesListView"
    v-else-if="pipelines.data && rows.length"
    v-model="pipelines.data.page_length_count"
    v-model:list="pipelines"
    :rows="rows"
    :columns="displayColumns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: pipelines.data.row_count,
      totalCount: pipelines.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
  />
  <div v-else-if="pipelines.data" class="flex h-full items-center justify-center">
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <PipelinesIcon class="h-10 w-10" />
      <span>{{ __('No {0} Found', [__('Pipelines')]) }}</span>
      <Button
        :label="__('Create')"
        iconLeft="plus"
        @click="showPipelineModal = true"
      />
    </div>
  </div>

  <!-- Success Toast -->
  <Toast
    v-if="showSuccessToast"
    :title="successMessage"
    @close="showSuccessToast = false"
  />

  <!-- Inline Pipeline Modal -->
  <Dialog v-model="showPipelineModal" :options="{ size: '3xl' }">
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
              variant="ghost"
              class="w-7"
              @click="showPipelineModal = false"
              icon="x"
            />
          </div>
        </div>
        <div>
          <!-- Form Fields -->
          <div class="space-y-4">
            <!-- Pipeline Name -->
            <div>
              <label class="text-sm font-medium text-ink-gray-7">
                {{ __('Pipeline Name') }} <span class="text-red-500">*</span>
              </label>
              <Input
                v-model="newPipeline.pipeline_name"
                type="text"
                class="mt-1"
                :placeholder="__('Enter pipeline name')"
                required
              />
            </div>

            <!-- Organization -->
            <div>
              <label class="text-sm font-medium text-ink-gray-7">
                {{ __('Organization') }}
              </label>
              <Input
                v-model="newPipeline.organization"
                type="text"
                class="mt-1"
                :placeholder="__('Enter organization name')"
              />
            </div>

            <!-- Status -->
            <div>
              <label class="text-sm font-medium text-ink-gray-7">
                {{ __('Status') }} <span class="text-red-500">*</span>
              </label>
              <Autocomplete
                v-model="newPipeline.status"
                :options="pipelineStatuses"
                class="mt-1"
                required
              />
            </div>

            <!-- Pipeline Owner -->
            <div>
              <label class="text-sm font-medium text-ink-gray-7">
                {{ __('Pipeline Owner') }}
              </label>
              <Input
                v-model="newPipeline.pipeline_owner"
                type="text"
                class="mt-1"
                :placeholder="__('Enter pipeline owner')"
              />
            </div>

            <!-- Email -->
            <div>
              <label class="text-sm font-medium text-ink-gray-7">
                {{ __('Email') }}
              </label>
              <Input
                v-model="newPipeline.email"
                type="email"
                class="mt-1"
                :placeholder="__('Enter email address')"
              />
            </div>

            <!-- Mobile No -->
            <!-- <div>
              <label class="text-sm font-medium text-ink-gray-7">
                {{ __('Mobile No') }}
              </label>
              <Input
                v-model="newPipeline.mobile_no"
                type="tel"
                class="mt-1"
                :placeholder="__('Enter mobile number')"
              />
            </div> -->

            <!-- Website -->
            <!-- <div>
              <label class="text-sm font-medium text-ink-gray-7">
                {{ __('Website') }}
              </label>
              <Input
                v-model="newPipeline.website"
                type="url"
                class="mt-1"
                :placeholder="__('Enter website URL')"
              />
            </div> -->
          </div>

          <ErrorMessage class="mt-4" v-if="pipelineError" :message="__(pipelineError)" />
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
          <Button
            variant="outline"
            :label="__('Cancel')"
            @click="showPipelineModal = false"
          />
        </div>
      </div>
    </template>
  </Dialog>

  <NoteModal
    v-if="showNoteModal"
    v-model="showNoteModal"
    :note="note"
    doctype="CRM Pipeline"
    :doc="docname"
  />
  <TaskModal
    v-if="showTaskModal"
    v-model="showTaskModal"
    :task="task"
    doctype="CRM Pipeline"
    :doc="docname"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import CustomActions from '@/components/CustomActions.vue'
import EmailAtIcon from '@/components/Icons/EmailAtIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import PipelinesIcon from '@/components/Icons/DealsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PipelinesListView from '@/components/ListViews/PipelinesListView.vue'
import KanbanView from '@/components/Kanban/KanbanView.vue'
import NoteModal from '@/components/Modals/NoteModal.vue'
import TaskModal from '@/components/Modals/TaskModal.vue'
import ViewControls from '@/components/ViewControls.vue'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { callEnabled } from '@/composables/settings'
import { formatDate, timeAgo, website, formatTime } from '@/utils'
import { Avatar, Tooltip, Dropdown, Dialog, Input, Autocomplete, ErrorMessage, Toast } from 'frappe-ui'
import { useRoute, useRouter } from 'vue-router'
import { ref, computed, reactive, h, watch, onMounted } from 'vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('CRM Pipeline')
const { makeCall } = globalStore()
const { getUser } = usersStore()

// Safe pipeline status function
function getPipelineStatus(status) {
  try {
    const { getPipelineStatus: getStatus } = statusesStore()
    const result = getStatus(status)
    return result || { color: 'gray' }
  } catch (error) {
    console.warn('getPipelineStatus not available, using default')
    // Fallback color mapping
    const statusColors = {
      'Open': 'green',
      'In Progress': 'blue', 
      'Closed': 'gray',
      'Won': 'green',
      'Lost': 'red',
      'Qualified': 'purple',
      'Ongoing': 'blue'
    }
    return {
      color: statusColors[status] || 'gray'
    }
  }
}

const route = useRoute()
const router = useRouter()

const pipelinesListView = ref(null)
const showPipelineModal = ref(false)
const isPipelineCreating = ref(false)
const pipelineError = ref(null)
const showSuccessToast = ref(false)
const successMessage = ref('')

const defaults = reactive({})

// New pipeline data
const newPipeline = reactive({
  pipeline_name: '',
  organization: '',
  status: 'Open',
  pipeline_owner: '',
  email: '',
  mobile_no: '',
  website: ''
})

// Pipeline status options
const pipelineStatuses = computed(() => {
  try {
    const { statusOptions } = statusesStore()
    let statuses = statusOptions('pipeline') || []
    if (statuses.length === 0) {
      // Fallback statuses if none are defined
      statuses = [
        { value: 'Open', label: 'Open' },
        { value: 'In Progress', label: 'In Progress' },
        { value: 'Ongoing', label: 'Ongoing' },
        { value: 'Completed', label: 'Completed' },
        { value: 'Closed', label: 'Closed' }
      ]
    }
    return statuses
  } catch (error) {
    console.warn('Error getting pipeline statuses:', error)
    return [
      { value: 'Open', label: 'Open' },
      { value: 'In Progress', label: 'In Progress' },
      { value: 'Ongoing', label: 'Ongoing' },
      { value: 'Completed', label: 'Completed' }
    ]
  }
})

// pipelines data is loaded in the ViewControls component
const pipelines = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

// Column persistence - simple approach
const savedColumns = ref(null)

// Load saved columns on mount
onMounted(() => {
  const saved = localStorage.getItem('crm_pipeline_columns')
  if (saved) {
    try {
      savedColumns.value = JSON.parse(saved)
      console.log('Loaded saved columns from localStorage')
    } catch (e) {
      console.error('Error loading saved columns:', e)
      savedColumns.value = null
    }
  }
  
  // Set default pipeline owner
  if (!newPipeline.pipeline_owner) {
    newPipeline.pipeline_owner = getUser().name
  }
})

// Use saved columns or API columns
const displayColumns = computed(() => {
  return savedColumns.value || pipelines.value?.data?.columns || []
})

// Save columns with debouncing to prevent loops
let saveTimeout = null
watch(() => pipelines.value?.data?.columns, (newColumns) => {
  if (!newColumns || newColumns.length === 0) return
  
  // Debounce the save to prevent multiple rapid saves
  clearTimeout(saveTimeout)
  saveTimeout = setTimeout(() => {
    // Convert to plain object and save
    try {
      const plainColumns = JSON.parse(JSON.stringify(newColumns))
      const newColumnsStr = JSON.stringify(plainColumns)
      const currentSavedStr = JSON.stringify(savedColumns.value)
      
      // Only save if columns actually changed
      if (newColumnsStr !== currentSavedStr) {
        savedColumns.value = plainColumns
        localStorage.setItem('crm_pipeline_columns', newColumnsStr)
        console.log('Columns saved successfully')
      }
    } catch (e) {
      console.error('Error saving columns:', e)
    }
  }, 300) // 300ms debounce
}, { deep: true })

function getRow(name, field) {
  function getValue(value) {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return value
    }
    return { label: value }
  }
  const row = rows.value?.find((row) => row.name == name)
  return row ? getValue(row[field]) : { label: '' }
}

// Rows
const rows = computed(() => {
  if (!pipelines.value?.data?.data) return []
  if (pipelines.value.data.view_type === 'group_by') {
    if (!pipelines.value?.data.group_by_field?.fieldname) return []
    return getGroupedByRows(
      pipelines.value?.data.data,
      pipelines.value?.data.group_by_field,
      pipelines.value.data.columns,
    )
  } else if (pipelines.value.data.view_type === 'kanban') {
    return getKanbanRows(pipelines.value.data.data, pipelines.value.data.fields)
  } else {
    return parseRows(pipelines.value?.data.data, pipelines.value.data.columns)
  }
})

function getGroupedByRows(listRows, groupByField, columns) {
  let groupedRows = []

  const options = groupByField.options || []
  options.forEach((option) => {
    let filteredRows = []

    if (!option) {
      filteredRows = listRows.filter((row) => !row[groupByField.fieldname])
    } else {
      filteredRows = listRows.filter(
        (row) => row[groupByField.fieldname] == option,
      )
    }

    let groupDetail = {
      label: groupByField.label,
      group: option || __(' '),
      collapsed: false,
      rows: parseRows(filteredRows, columns),
    }
    if (groupByField.fieldname == 'status') {
      groupDetail.icon = () =>
        h(IndicatorIcon, {
          class: getPipelineStatus(option).color,
        })
    }
    groupedRows.push(groupDetail)
  })

  return groupedRows || listRows
}

function getKanbanRows(data, columns) {
  let _rows = []
  data.forEach((column) => {
    column.data?.forEach((row) => {
      _rows.push(row)
    })
  })
  return parseRows(_rows, columns)
}

function parseRows(rows, columns = []) {
  let view_type = pipelines.value.data.view_type
  let key = view_type === 'kanban' ? 'fieldname' : 'key'
  let type = view_type === 'kanban' ? 'fieldtype' : 'type'

  return rows.map((pipeline) => {
    let _rows = {}
    const rowFields = pipelines.value?.data.rows || []
    
    rowFields.forEach((row) => {
      _rows[row] = pipeline[row]

      let fieldType = columns?.find((col) => (col[key] || col.value) == row)?.[
        type
      ]

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(pipeline[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, pipeline)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, pipeline)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, pipeline)
      }

      if (row == 'pipeline_name') {
        _rows[row] = {
          label: pipeline.pipeline_name,
          image: pipeline.image,
          image_label: pipeline.lead_name || pipeline.pipeline_name,
        }
      } else if (row == 'organization') {
        _rows[row] = pipeline.organization
      } else if (row === 'website') {
        _rows[row] = website(pipeline.website)
      } else if (row == 'status') {
        _rows[row] = {
          label: pipeline.status,
          color: getPipelineStatus(pipeline.status).color,
        }
      } else if (row == 'pipeline_owner') {
        _rows[row] = {
          label: pipeline.pipeline_owner && getUser(pipeline.pipeline_owner).full_name,
          ...(pipeline.pipeline_owner && getUser(pipeline.pipeline_owner)),
        }
      } else if (row == '_assign') {
        let assignees = JSON.parse(pipeline._assign || '[]')
        _rows[row] = assignees.map((user) => ({
          name: user,
          image: getUser(user).user_image,
          label: getUser(user).full_name,
        }))
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: formatDate(pipeline[row]),
          timeAgo: __(timeAgo(pipeline[row])),
        }
      } else if (['est_pipeline_value', 'total_deal_value'].includes(row)) {
        _rows[row] = {
          label: pipeline[row] ? formatCurrency(pipeline[row]) : '',
          value: pipeline[row]
        }
      }
    })
    _rows['_email_count'] = pipeline._email_count || 0
    _rows['_note_count'] = pipeline._note_count || 0
    _rows['_task_count'] = pipeline._task_count || 0
    _rows['_comment_count'] = pipeline._comment_count || 0
    return _rows
  })
}

function formatCurrency(value) {
  if (!value) return ''
  // Simple currency formatting
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(parseFloat(value))
}

function onNewClick(column) {
  let column_field = pipelines.value.params?.column_field

  if (column_field) {
    defaults[column_field] = column.column.name
  }

  showPipelineModal.value = true
}

function actions(itemName) {
  let mobile_no = getRow(itemName, 'mobile_no')?.label || ''
  let actions = [
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: __('Make a Call'),
      onClick: () => makeCall(mobile_no),
      condition: () => mobile_no && callEnabled.value,
    },
    {
      icon: h(NoteIcon, { class: 'h-4 w-4' }),
      label: __('New Note'),
      onClick: () => showNote(itemName),
    },
    {
      icon: h(TaskIcon, { class: 'h-4 w-4' }),
      label: __('New Task'),
      onClick: () => showTask(itemName),
    },
  ]
  return actions.filter((action) =>
    action.condition ? action.condition() : true,
  )
}

const docname = ref('')
const showNoteModal = ref(false)
const note = ref({
  title: '',
  content: '',
})

function showNote(name) {
  docname.value = name
  showNoteModal.value = true
}

const showTaskModal = ref(false)
const task = ref({
  title: '',
  description: '',
  assigned_to: '',
  due_date: '',
  priority: 'Low',
  status: 'Backlog',
})

function showTask(name) {
  docname.value = name
  showTaskModal.value = true
}

// Create new pipeline function - NO VALIDATION FOR EMAIL AND PHONE
async function createNewPipeline() {
  // Reset error
  pipelineError.value = null
  
  // Validate required fields only
  if (!newPipeline.pipeline_name) {
    pipelineError.value = __('Pipeline Name is mandatory')
    return
  }
  
  if (!newPipeline.status) {
    pipelineError.value = __('Status is required')
    return
  }

  // Auto-fix website format if provided
  if (newPipeline.website && !newPipeline.website.startsWith('http')) {
    newPipeline.website = 'https://' + newPipeline.website
  }

  isPipelineCreating.value = true

  try {
    const response = await fetch('/api/method/frappe.client.insert', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': window.csrf_token || await getCSRFToken()
      },
      body: JSON.stringify({
        doc: {
          doctype: 'CRM Pipeline',
          ...newPipeline,
        }
      })
    })
    
    const result = await response.json()
    
    if (!response.ok) {
      throw new Error(result.message || 'Failed to create pipeline')
    }

    if (result.exc) {
      throw new Error('Server error occurred while creating pipeline')
    }

    isPipelineCreating.value = false
    showPipelineModal.value = false
    
    // Show success message
    successMessage.value = __('Pipeline created successfully')
    showSuccessToast.value = true
    
    // Reset form
    resetPipelineForm()
    
    // Refresh the pipelines list
    if (viewControls.value && viewControls.value.refresh) {
      viewControls.value.refresh()
    }
    
    // Force page reload to ensure data is fresh
    setTimeout(() => {
      window.location.reload()
    }, 1000)
    
  } catch (err) {
    isPipelineCreating.value = false
    console.error('Error creating pipeline:', err)
    
    if (err.messages) {
      pipelineError.value = err.messages.join('\n')
    } else if (err.message) {
      pipelineError.value = err.message
    } else {
      pipelineError.value = __('Failed to create pipeline. Please try again.')
    }
  }
}

// Helper function to get CSRF token
async function getCSRFToken() {
  try {
    const response = await fetch('/api/method/frappe.csrf_token.get_token')
    const data = await response.json()
    return data.csrf_token
  } catch (error) {
    console.error('Error getting CSRF token:', error)
    return ''
  }
}

// Reset form function
function resetPipelineForm() {
  Object.assign(newPipeline, {
    pipeline_name: '',
    organization: '',
    status: 'Open',
    pipeline_owner: getUser().name,
    email: '',
    mobile_no: '',
    website: ''
  })
  pipelineError.value = null
}

// Watch for modal close and reset form
watch(showPipelineModal, (newVal) => {
  if (!newVal) {
    resetPipelineForm()
  }
})
</script>
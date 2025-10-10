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
  <PipelineModal
    v-if="showPipelineModal"
    v-model="showPipelineModal"
    :defaults="defaults"
  />
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
import PipelineModal from '@/components/Modals/PipelineModal.vue'
import NoteModal from '@/components/Modals/NoteModal.vue'
import TaskModal from '@/components/Modals/TaskModal.vue'
import ViewControls from '@/components/ViewControls.vue'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { callEnabled } from '@/composables/settings'
import { formatDate, timeAgo, website, formatTime } from '@/utils'
import { Avatar, Tooltip, Dropdown } from 'frappe-ui'
import { useRoute } from 'vue-router'
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
      'Qualified': 'purple'
    }
    return {
      color: statusColors[status] || 'gray'
    }
  }
}

const route = useRoute()

const pipelinesListView = ref(null)
const showPipelineModal = ref(false)

const defaults = reactive({})

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
</script>
<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Sticky Header -->
    <div class="sticky top-0 z-10 bg-white border-b border-gray-200">
      <div class="px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <button 
              @click="router.back()"
              class="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
              </svg>
            </button>
            <div>
              <h1 class="text-2xl font-semibold text-gray-900">{{ pipeline.pipeline_name || pipeline.name }}</h1>
              <div class="flex items-center space-x-4 mt-1">
                <span class="text-sm text-gray-500">Pipeline</span>
                <span class="text-sm text-gray-500">•</span>
                <span class="text-sm text-gray-500">{{ pipeline.name }}</span>
              </div>
            </div>
          </div>
          <div class="flex items-center space-x-3">
            <!-- Status Change Dropdown -->
            <div class="relative" ref="statusDropdown">
              <button 
                @click="toggleStatusDropdown"
                class="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors text-sm font-medium"
              >
                <span :class="getStatusClasses(pipeline.status)" class="px-2 py-1 rounded-full text-xs font-medium">
                  {{ pipeline.status }}
                </span>
                <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
              </button>

              <!-- Status Dropdown Menu -->
              <div 
                v-if="showStatusDropdown"
                class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20"
              >
                <button 
                  v-for="status in pipelineStatuses"
                  :key="status"
                  @click="changeStatus(status)"
                  :disabled="status === pipeline.status"
                  class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span :class="getStatusClasses(status)" class="px-2 py-1 rounded-full text-xs font-medium">
                    {{ status }}
                  </span>
                  <span v-if="status === pipeline.status" class="text-blue-600 text-xs">Current</span>
                </button>
              </div>
            </div>

            <button 
              @click="convertToDeal"
              :disabled="converting"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span v-if="converting">Converting...</span>
              <span v-else>Convert to Deal</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-6 py-6">
      <div class="grid grid-cols-3 gap-6">
        <!-- Left Column - Main Content -->
        <div class="col-span-2 space-y-6">
          <!-- Status Card -->
          <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div class="p-6">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-medium text-gray-900">Pipeline Status</h3>
                <span :class="getStatusClasses(pipeline.status)" class="px-3 py-1 rounded-full text-sm font-medium">
                  {{ pipeline.status }}
                </span>
              </div>
              
              <div class="grid grid-cols-3 gap-4">
                <div class="text-center p-4 bg-gray-50 rounded-lg">
                  <div class="text-2xl font-bold text-gray-900">{{ formatCurrency(pipeline.est_pipeline_value) }}</div>
                  <div class="text-sm text-gray-500 mt-1">Estimated Value</div>
                </div>
                <div class="text-center p-4 bg-gray-50 rounded-lg">
                  <div class="text-2xl font-bold text-gray-900">{{ pipeline.deals?.length || 0 }}</div>
                  <div class="text-sm text-gray-500 mt-1">Total Deals</div>
                </div>
                <div class="text-center p-4 bg-gray-50 rounded-lg">
                  <div class="text-2xl font-bold text-gray-900">{{ formatCurrency(calculateTotalDealValue()) }}</div>
                  <div class="text-sm text-gray-500 mt-1">Actual Value</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Deals Section -->
          <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div class="p-6">
              <div class="flex items-center justify-between mb-6">
                <h3 class="text-lg font-medium text-gray-900">Deals</h3>
                <div class="text-sm text-gray-500">{{ pipeline.deals?.length || 0 }} deals</div>
              </div>

              <div v-if="pipeline.deals && pipeline.deals.length" class="space-y-4">
                <div 
                  v-for="deal in pipeline.deals" 
                  :key="deal.deal"
                  class="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
                >
                  <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center space-x-3">
                      <div class="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center text-white font-medium text-sm">
                        D
                      </div>
                      <div>
                        <div class="font-medium text-gray-900">{{ deal.deal }}</div>
                        <div class="text-sm text-gray-500">Probability: {{ deal.probablity }}%</div>
                      </div>
                    </div>
                    <div class="text-right">
                      <div class="font-semibold text-gray-900">{{ formatCurrency(deal.est_qoutation_sales) }}</div>
                      <div class="text-sm text-gray-500">Expected: {{ deal.expected_deal_value }}%</div>
                    </div>
                  </div>
                  
                  <div class="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div class="text-gray-500">Deal Value</div>
                      <div class="font-medium text-gray-900">{{ formatCurrency(deal.deal_value) }}</div>
                    </div>
                    <div>
                      <div class="text-gray-500">Quotation Sales</div>
                      <div class="font-medium text-gray-900">{{ formatCurrency(deal.est_qoutation_sales) }}</div>
                    </div>
                    <div>
                      <div class="text-gray-500">Owner</div>
                      <div class="font-medium text-gray-900">{{ deal.deal_owner || 'Unassigned' }}</div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div v-else class="text-center py-8">
                <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                  </svg>
                </div>
                <h3 class="text-lg font-medium text-gray-900 mb-2">No deals yet</h3>
                <p class="text-gray-500 text-sm mb-4">Convert this pipeline to create deals</p>
                <button 
                  @click="convertToDeal"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                >
                  Convert to Deal
                </button>
              </div>
            </div>
          </div>

          <!-- Status Logs Table -->
          <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div class="p-6">
              <div class="flex items-center justify-between mb-6">
                <h3 class="text-lg font-medium text-gray-900">Status Change History</h3>
                <button 
                  @click="fetchPipeline"
                  :disabled="loading"
                  class="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  title="Refresh logs"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                  </svg>
                </button>
              </div>
              
              <div v-if="pipeline.logs && pipeline.logs.length" class="overflow-hidden">
                <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-50">
                    <tr>
                      <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Change Date
                      </th>
                      <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        From Status
                      </th>
                      <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        To Status
                      </th>
                      <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Duration
                      </th>
                      <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Log Owner
                      </th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <tr 
                      v-for="log in sortedLogs" 
                      :key="log.name"
                      class="hover:bg-gray-50 transition-colors"
                    >
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {{ formatDateTime(log.from_date) }}
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap">
                        <span :class="getStatusClasses(log.from_status)" class="px-2 py-1 rounded-full text-xs font-medium">
                          {{ log.from_status || '—' }}
                        </span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap">
                        <span :class="getStatusClasses(log.to_status)" class="px-2 py-1 rounded-full text-xs font-medium">
                          {{ log.to_status || '—' }}
                        </span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {{ formatDuration(log.duration) }}
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div class="flex items-center space-x-2">
                          <div class="w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center text-xs text-white font-medium">
                            {{ getInitials(log.log_owner) }}
                          </div>
                          <span>{{ log.log_owner || 'System' }}</span>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              <div v-else class="text-center py-8">
                <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                </div>
                <p class="text-gray-500 text-sm">No status change history available</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column - Sidebar -->
        <div class="space-y-6">
          <!-- Pipeline Information -->
          <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div class="p-6">
              <h3 class="text-lg font-medium text-gray-900 mb-4">Pipeline Information</h3>
              
              <div class="space-y-4">
                <div>
                  <label class="text-sm font-medium text-gray-500">Pipeline Owner</label>
                  <div class="flex items-center space-x-2 mt-1">
                    <div class="w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center text-xs text-white font-medium">
                      {{ getInitials(pipeline.pipeline_owner) }}
                    </div>
                    <span class="text-sm text-gray-900">{{ pipeline.pipeline_owner }}</span>
                  </div>
                </div>
                
                <div>
                  <label class="text-sm font-medium text-gray-500">Source</label>
                  <div class="text-sm text-gray-900 mt-1">{{ pipeline.source || '—' }}</div>
                </div>
                
                <div>
                  <label class="text-sm font-medium text-gray-500">Created</label>
                  <div class="text-sm text-gray-900 mt-1">{{ formatDate(pipeline.creation) }}</div>
                </div>
                
                <div>
                  <label class="text-sm font-medium text-gray-500">Last Modified</label>
                  <div class="text-sm text-gray-900 mt-1">{{ formatDate(pipeline.modified) }}</div>
                </div>
                
                <div>
                  <label class="text-sm font-medium text-gray-500">Currency</label>
                  <div class="text-sm text-gray-900 mt-1">{{ pipeline.currency || 'USD' }}</div>
                </div>
                
                <div>
                  <label class="text-sm font-medium text-gray-500">Exchange Rate</label>
                  <div class="text-sm text-gray-900 mt-1">{{ pipeline.exchange_rate || '1.0' }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Organization Details -->
          <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div class="p-6">
              <h3 class="text-lg font-medium text-gray-900 mb-4">Organization</h3>
              
              <div class="space-y-4">
                <div>
                  <label class="text-sm font-medium text-gray-500">Organization Name</label>
                  <div class="text-sm text-gray-900 mt-1">{{ pipeline.organization_name || pipeline.organization }}</div>
                </div>
                
                <div>
                  <label class="text-sm font-medium text-gray-500">Website</label>
                  <div class="text-sm text-gray-900 mt-1">
                    <a :href="pipeline.website" target="_blank" class="text-blue-600 hover:text-blue-700">
                      {{ pipeline.website || '—' }}
                    </a>
                  </div>
                </div>
                
                <div>
                  <label class="text-sm font-medium text-gray-500">Employees</label>
                  <div class="text-sm text-gray-900 mt-1">{{ pipeline.no_of_employees || '0' }}</div>
                </div>
                
                <div>
                  <label class="text-sm font-medium text-gray-500">Territory</label>
                  <div class="text-sm text-gray-900 mt-1">{{ pipeline.territory || '—' }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Lead Information -->
          <div v-if="pipeline.lead" class="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div class="p-6">
              <h3 class="text-lg font-medium text-gray-900 mb-4">Lead Information</h3>
              
              <div class="space-y-4">
                <div>
                  <label class="text-sm font-medium text-gray-500">Lead</label>
                  <div class="text-sm text-gray-900 mt-1">{{ pipeline.lead }}</div>
                </div>
                
                <div>
                  <label class="text-sm font-medium text-gray-500">Lead Name</label>
                  <div class="text-sm text-gray-900 mt-1">{{ pipeline.lead_name }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { call, toast } from 'frappe-ui'

const route = useRoute()
const router = useRouter()

const pipeline = ref({})
const pipelineStatuses = ref([])
const loading = ref(false)
const converting = ref(false)
const showStatusDropdown = ref(false)
const changingStatus = ref(false)
const statusDropdown = ref(null)

// Fetch pipeline statuses
async function fetchPipelineStatuses() {
  try {
    const result = await call('frappe.client.get_list', {
      doctype: 'CRM Pipeline Status',
      fields: ['name'],
      order_by: 'creation asc'
    })
    pipelineStatuses.value = result.map(status => status.name)
  } catch (error) {
    console.error('Error fetching pipeline statuses:', error)
    // Fallback to common statuses
    pipelineStatuses.value = [
      'Draft',
      'Active', 
      'In Progress',
      'On Hold',
      'Completed',
      'Lost',
      'Cancelled',
      'Open'
    ]
  }
}

// Fetch pipeline details
async function fetchPipeline() {
  loading.value = true
  try {
    const result = await call('frappe.client.get', {
      doctype: 'CRM Pipeline',
      name: route.params.pipelineId
    })
    pipeline.value = result
  } catch (error) {
    console.error('Error fetching pipeline:', error)
    toast.error('Failed to load pipeline details')
  } finally {
    loading.value = false
  }
}

// Toggle status dropdown
function toggleStatusDropdown() {
  showStatusDropdown.value = !showStatusDropdown.value
}

// Change pipeline status
async function changeStatus(newStatus) {
  if (newStatus === pipeline.value.status) {
    showStatusDropdown.value = false
    return
  }

  changingStatus.value = true
  try {
    // Call the API to update pipeline status
    await call('crm_pipeline.api.update_pipeline_status', {
      pipeline_name: pipeline.value.name,
      new_status: newStatus
    })
    
    toast.success(`Pipeline status changed to ${newStatus}`)
    showStatusDropdown.value = false
    
    // Refresh pipeline data to get updated status and logs
    await fetchPipeline()
    
  } catch (error) {
    console.error('Error changing pipeline status:', error)
    toast.error('Failed to change pipeline status')
  } finally {
    changingStatus.value = false
  }
}

// Convert pipeline to deal
async function convertToDeal() {
  converting.value = true
  try {
    await call('crm_pipeline.api.create_deal_from_pipeline', {
      pipeline_name: pipeline.value.name
    })
    
    toast.success('Pipeline converted to deal successfully')
    await fetchPipeline()
    
  } catch (error) {
    console.error('Error converting pipeline:', error)
    toast.error('Failed to convert pipeline to deal')
  } finally {
    converting.value = false
  }
}

// Calculate total deal value from all deals
function calculateTotalDealValue() {
  if (!pipeline.value.deals || !pipeline.value.deals.length) return 0
  return pipeline.value.deals.reduce((total, deal) => total + (deal.deal_value || 0), 0)
}

// Sort logs by from_date (newest first)
const sortedLogs = computed(() => {
  if (!pipeline.value.logs) return []
  return [...pipeline.value.logs].sort((a, b) => new Date(b.from_date) - new Date(a.from_date))
})

// Format duration
function formatDuration(duration) {
  if (!duration || duration === '0.000000000') return '—'
  const seconds = parseFloat(duration)
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  else if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`
  else if (seconds < 86400) return `${(seconds / 3600).toFixed(1)}h`
  else return `${(seconds / 86400).toFixed(1)}d`
}

// Close dropdown when clicking outside
function handleClickOutside(event) {
  if (statusDropdown.value && !statusDropdown.value.contains(event.target)) {
    showStatusDropdown.value = false
  }
}

// Helper functions
function getInitials(name) {
  if (!name) return '—'
  return name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)
}

function getStatusClasses(status) {
  const classes = {
    'Active': 'bg-green-100 text-green-800',
    'In Progress': 'bg-blue-100 text-blue-800',
    'Completed': 'bg-purple-100 text-purple-800',
    'Lost': 'bg-red-100 text-red-800',
    'Draft': 'bg-gray-100 text-gray-800',
    'On Hold': 'bg-yellow-100 text-yellow-800',
    'Cancelled': 'bg-gray-100 text-gray-800',
    'Open': 'bg-blue-100 text-blue-800'
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}

function formatCurrency(amount) {
  if (!amount) return '$0'
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(numAmount)
}

function formatDate(dateString) {
  if (!dateString) return '—'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    year: 'numeric'
  })
}

function formatDateTime(dateString) {
  if (!dateString) return '—'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Lifecycle
onMounted(() => {
  fetchPipelineStatuses()
  fetchPipeline()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* Custom styles */
.hover\:border-blue-300:hover {
  border-color: #93c5fd;
}

.transition-colors {
  transition: all 0.15s ease-in-out;
}

/* Table styling */
table {
  border-collapse: separate;
  border-spacing: 0;
}

th, td {
  border-bottom: 1px solid #e5e7eb;
}

/* Sticky header */
.sticky {
  position: sticky;
  z-index: 10;
}
</style>
<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Sticky Header -->
    <div class="sticky top-0 z-10 bg-white border-b border-gray-200">
      <div class="px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <h1 class="text-2xl font-semibold text-gray-900">Pipelines</h1>
            <div class="flex items-center space-x-2 text-sm text-gray-500">
              <span>{{ totalCount }} pipelines</span>
            </div>
          </div>
          <div class="flex items-center space-x-3">
            <button 
              @click="showPipelineModal = true"
              class="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
              </svg>
              <span>New Pipeline</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Sticky Filters -->
    <div class="sticky top-16 z-10 bg-white border-b border-gray-200">
      <div class="px-6 py-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <!-- Search -->
            <div class="relative">
              <input 
                v-model="searchQuery"
                type="text" 
                placeholder="Search pipelines..." 
                class="pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-80 text-sm"
                @input="debouncedSearch"
              >
              <svg class="w-4 h-4 text-gray-400 absolute left-3 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </div>

            <!-- Status Filter -->
            <select 
              v-model="statusFilter"
              @change="fetchPipelines"
              class="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
              <option value="">All Status</option>
              <option 
                v-for="status in pipelineStatuses" 
                :key="status"
                :value="status"
              >
                {{ status }}
              </option>
            </select>
          </div>

          <div class="flex items-center space-x-2">
            <!-- Refresh -->
            <button 
              @click="fetchPipelines"
              :disabled="loading"
              class="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              title="Refresh"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="p-8">
      <div class="bg-white rounded-lg border border-gray-200 p-8">
        <div class="flex items-center justify-center space-x-3">
          <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span class="text-gray-600 text-sm">Loading pipelines...</span>
        </div>
      </div>
    </div>

    <!-- Pipeline List -->
    <div v-else class="p-6">
      <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
        <!-- Table Header -->
        <div class="grid grid-cols-12 gap-4 px-6 py-3 border-b border-gray-200 bg-gray-50 text-xs font-medium text-gray-600 uppercase tracking-wider">
          <div class="col-span-4">Pipeline</div>
          <div class="col-span-2">Organization</div>
          <div class="col-span-1">Status</div>
          <div class="col-span-2">Owner</div>
          <div class="col-span-2 text-right">Value</div>
          <div class="col-span-1"></div>
        </div>

        <!-- Pipeline Items -->
        <div v-if="pipelines.length" class="divide-y divide-gray-200">
          <div 
            v-for="pipeline in pipelines" 
            :key="pipeline.name"
            class="grid grid-cols-12 gap-4 px-6 py-4 hover:bg-blue-50 transition-colors cursor-pointer group"
            @click="viewPipeline(pipeline.name)"
          >
            <!-- Pipeline Name -->
            <div class="col-span-4 flex items-center space-x-3">
              <div class="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center text-white font-medium text-sm">
                {{ getInitials(pipeline.pipeline_name || pipeline.name) }}
              </div>
              <div class="min-w-0 flex-1">
                <div class="flex items-center space-x-2">
                  <p class="text-sm font-medium text-gray-900 truncate">
                    {{ pipeline.pipeline_name || pipeline.name }}
                  </p>
                  <span v-if="pipeline._liked_by && isLiked(pipeline._liked_by)" class="text-red-500">
                    <svg class="w-4 h-4 fill-current" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clip-rule="evenodd"></path>
                    </svg>
                  </span>
                </div>
              </div>
            </div>

            <!-- Organization -->
            <div class="col-span-2 flex items-center">
              <div v-if="pipeline.organization" class="flex items-center space-x-2 max-w-full">
                <div class="w-6 h-6 bg-gray-200 rounded flex items-center justify-center text-xs text-gray-600 font-medium flex-shrink-0">
                  {{ getInitials(pipeline.organization) }}
                </div>
                <span class="text-sm text-gray-700 truncate">{{ pipeline.organization }}</span>
              </div>
              <span v-else class="text-sm text-gray-400">—</span>
            </div>

            <!-- Status -->
            <div class="col-span-1 flex items-center">
              <span :class="getStatusClasses(pipeline.status)" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
                {{ pipeline.status || '—' }}
              </span>
            </div>

            <!-- Owner -->
            <div class="col-span-2 flex items-center">
              <div v-if="pipeline.pipeline_owner" class="flex items-center space-x-2">
                <div class="w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center text-xs text-white font-medium">
                  {{ getInitials(pipeline.pipeline_owner) }}
                </div>
                <span class="text-sm text-gray-700">{{ getShortName(pipeline.pipeline_owner) }}</span>
              </div>
              <span v-else class="text-sm text-gray-400">—</span>
            </div>

            <!-- Value -->
            <div class="col-span-2 flex flex-col items-end space-y-1">
              <div v-if="pipeline.est_pipeline_value" class="text-sm font-medium text-gray-900">
                {{ formatCurrency(pipeline.est_pipeline_value) }}
              </div>
              <div v-if="pipeline.total_deal_value" class="text-xs text-gray-500">
                Actual: {{ formatCurrency(pipeline.total_deal_value) }}
              </div>
            </div>

            <!-- Actions -->
            <div class="col-span-1 flex items-center justify-end">
              <button 
                @click.stop="openPipelineActions(pipeline)"
                class="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-gray-600 transition-all"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-12">
          <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-900 mb-2">No pipelines found</h3>
          <p class="text-gray-500 text-sm mb-6 max-w-sm mx-auto">
            {{ searchQuery || statusFilter ? 'Try adjusting your search or filter to find what you are looking for.' : 'Get started by creating your first pipeline to track your sales process.' }}
          </p>
          <button 
            @click="showPipelineModal = true"
            class="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            <span>New Pipeline</span>
          </button>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="pipelines.length" class="flex items-center justify-between mt-6 px-2">
        <div class="text-sm text-gray-700">
          Showing <span class="font-medium">{{ startIndex + 1 }}</span> to 
          <span class="font-medium">{{ endIndex }}</span> of 
          <span class="font-medium">{{ totalCount }}</span> results
        </div>
        <div class="flex items-center space-x-1">
          <button 
            @click="previousPage"
            :disabled="currentPage === 1"
            class="px-3 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors flex items-center space-x-1 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
            </svg>
            <span>Previous</span>
          </button>
          <button 
            v-for="page in visiblePages"
            :key="page"
            @click="goToPage(page)"
            :class="[
              'px-3 py-2 border rounded-lg transition-colors text-sm',
              currentPage === page 
                ? 'bg-blue-600 text-white border-blue-600' 
                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
            ]"
          >
            {{ page }}
          </button>
          <button 
            @click="nextPage"
            :disabled="currentPage === totalPages"
            class="px-3 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors flex items-center space-x-1 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            <span>Next</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Pipeline Creation Modal -->
    <div v-if="showPipelineModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        <!-- Modal Header -->
        <div class="px-6 py-4 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-medium text-gray-900">Create New Pipeline</h3>
            <button 
              @click="showPipelineModal = false"
              class="p-2 text-gray-400 hover:text-gray-600 rounded-lg transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>

        <!-- Tabs -->
        <div class="border-b border-gray-200">
          <nav class="flex space-x-8 px-6">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'py-4 px-1 border-b-2 font-medium text-sm transition-colors',
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              {{ tab.name }}
            </button>
          </nav>
        </div>

        <!-- Modal Content -->
        <div class="flex-1 overflow-y-auto">
          <form @submit.prevent="createNewPipeline" class="p-6">
            <!-- Basic Information Tab -->
            <div v-if="activeTab === 'basic'" class="space-y-6">
              <div class="grid grid-cols-2 gap-6">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Pipeline Name <span class="text-red-500">*</span>
                  </label>
                  <input 
                    v-model="newPipelineForm.pipeline_name"
                    type="text" 
                    required
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter pipeline name"
                  />
                </div>
              

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Organization</label>
                  <input 
                    v-model="newPipelineForm.organization"
                    type="text" 
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter organization name"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Pipeline Owner</label>
                  <input 
                    v-model="newPipelineForm.pipeline_owner"
                    type="text" 
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter owner email"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Source</label>
                  <select 
                    v-model="newPipelineForm.source"
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select Source</option>
                    <option value="Cold Calling">Cold Calling</option>
                    <option value="Email Campaign">Email Campaign</option>
                    <option value="Referral">Referral</option>
                    <option value="Website">Website</option>
                    <option value="Social Media">Social Media</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Territory</label>
                  <input 
                    v-model="newPipelineForm.territory"
                    type="text" 
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter territory"
                  />
                </div>
              </div>

              <div class="grid grid-cols-2 gap-6">

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Mobile No</label>
                  <input 
                    v-model="newPipelineForm.mobile_no"
                    type="tel" 
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter mobile number"
                  />
                </div>
              </div>
            </div>

            <!-- Financial Information Tab -->
            <div v-if="activeTab === 'financial'" class="space-y-6">
              <div class="grid grid-cols-2 gap-6">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Estimated Pipeline Value</label>
                  <input 
                    v-model="newPipelineForm.est_pipeline_value"
                    type="number" 
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter estimated value"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Currency</label>
                  <select 
                    v-model="newPipelineForm.currency"
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="GBP">GBP</option>
                    <option value="INR">INR</option>
                    <option value="JPY">JPY</option>
                  </select>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Exchange Rate</label>
                  <input 
                    v-model="newPipelineForm.exchange_rate"
                    type="number" 
                    step="0.01"
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="1.0"
                    value="1.0"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Total Deal Value</label>
                  <input 
                    v-model="newPipelineForm.total_deal_value"
                    type="number" 
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter total deal value"
                  />
                </div>
              </div>
            </div>

            <!-- Additional Information Tab -->
            <div v-if="activeTab === 'additional'" class="space-y-6">
              <div class="grid grid-cols-2 gap-6">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Website</label>
                  <input 
                    v-model="newPipelineForm.website"
                    type="url" 
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="https://example.com"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">No of Employees</label>
                  <input 
                    v-model="newPipelineForm.no_of_employees"
                    type="number" 
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter number of employees"
                  />
                </div>

                <div class="col-span-2">
                  <label class="block text-sm font-medium text-gray-700 mb-2">Lead</label>
                  <input 
                    v-model="newPipelineForm.lead"
                    type="text" 
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter lead reference"
                  />
                </div>

                <div class="col-span-2">
                  <label class="block text-sm font-medium text-gray-700 mb-2">Lead Name</label>
                  <input 
                    v-model="newPipelineForm.lead_name"
                    type="text" 
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter lead name"
                  />
                </div>
              </div>
            </div>

            <!-- Form Actions -->
            <div class="flex justify-between items-center pt-6 border-t border-gray-200">
              <div class="flex space-x-3">
                <button 
                  v-if="activeTab !== 'basic'"
                  type="button"
                  @click="previousTab"
                  class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors text-sm font-medium"
                >
                  Previous
                </button>
                <button 
                  v-if="activeTab !== 'additional'"
                  type="button"
                  @click="nextTab"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                >
                  Next
                </button>
              </div>
              
              <div class="flex space-x-3">
                <button 
                  type="button"
                  @click="showPipelineModal = false"
                  class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors text-sm font-medium"
                >
                  Cancel
                </button>
                <button 
                  v-if="activeTab === 'additional'"
                  type="submit"
                  :disabled="creatingPipeline"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50"
                >
                  <span v-if="creatingPipeline">Creating...</span>
                  <span v-else>Create Pipeline</span>
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { call, toast } from 'frappe-ui'

const router = useRouter()

// Reactive data
const pipelines = ref([])
const pipelineStatuses = ref([])
const loading = ref(false)
const creatingPipeline = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)
const showPipelineModal = ref(false)
const activeTab = ref('basic')

// Tabs configuration
const tabs = [
  { id: 'basic', name: 'Basic Information' },
  { id: 'financial', name: 'Financial Information' },
  { id: 'additional', name: 'Additional Information' }
]

// New pipeline form with all fields
const newPipelineForm = ref({
  // Basic Information
  pipeline_name: '',
  status: 'Open',
  organization: '',
  pipeline_owner: '',
  source: '',
  territory: '',
  mobile_no: '',
  
  // Financial Information
  est_pipeline_value: '',
  currency: 'USD',
  exchange_rate: '1.0',
  total_deal_value: '',
  
  // Additional Information
  website: '',
  no_of_employees: '',
  lead: '',
  lead_name: ''
})

// Computed properties
const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value))
const startIndex = computed(() => (currentPage.value - 1) * pageSize.value)
const endIndex = computed(() => Math.min(startIndex.value + pageSize.value, totalCount.value))

const visiblePages = computed(() => {
  const pages = []
  const start = Math.max(1, currentPage.value - 2)
  const end = Math.min(totalPages.value, start + 4)
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

// Fetch pipeline statuses from CRM Pipeline Status doctype
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

// Fetch pipelines from Frappe backend
async function fetchPipelines() {
  loading.value = true
  try {
    const filters = {}
    
    if (searchQuery.value) {
      filters.pipeline_name = ['like', `%${searchQuery.value}%`]
    }
    
    if (statusFilter.value) {
      filters.status = statusFilter.value
    }

    const result = await call('frappe.client.get_list', {
      doctype: 'CRM Pipeline',
      fields: [
        'name',
        'pipeline_name',
        'organization',
        'status',
        'pipeline_owner',
        'est_pipeline_value',
        'total_deal_value',
        'modified',
        '_liked_by'
      ],
      filters: filters,
      limit_start: startIndex.value,
      limit_page_length: pageSize.value,
      order_by: 'modified desc'
    })

    pipelines.value = result
    totalCount.value = await getTotalCount(filters)
    
  } catch (error) {
    console.error('Error fetching pipelines:', error)
    toast.error('Failed to load pipelines')
  } finally {
    loading.value = false
  }
}

// Get total count for pagination
async function getTotalCount(filters) {
  try {
    const result = await call('frappe.client.get_count', {
      doctype: 'CRM Pipeline',
      filters: filters
    })
    return result
  } catch (error) {
    console.error('Error getting count:', error)
    return 0
  }
}

// Tab navigation
function nextTab() {
  const currentIndex = tabs.findIndex(tab => tab.id === activeTab.value)
  if (currentIndex < tabs.length - 1) {
    activeTab.value = tabs[currentIndex + 1].id
  }
}

function previousTab() {
  const currentIndex = tabs.findIndex(tab => tab.id === activeTab.value)
  if (currentIndex > 0) {
    activeTab.value = tabs[currentIndex - 1].id
  }
}

// Create new pipeline
async function createNewPipeline() {
  creatingPipeline.value = true
  try {
    // Prepare the document data
    const docData = {
      doctype: 'CRM Pipeline',
      pipeline_name: newPipelineForm.value.pipeline_name,
      status: newPipelineForm.value.status,
      organization: newPipelineForm.value.organization || undefined,
      pipeline_owner: newPipelineForm.value.pipeline_owner || undefined,
      source: newPipelineForm.value.source || undefined,
      territory: newPipelineForm.value.territory || undefined,
      mobile_no: newPipelineForm.value.mobile_no || undefined,
      est_pipeline_value: newPipelineForm.value.est_pipeline_value || undefined,
      currency: newPipelineForm.value.currency,
      exchange_rate: parseFloat(newPipelineForm.value.exchange_rate) || 1.0,
      total_deal_value: newPipelineForm.value.total_deal_value || undefined,
      website: newPipelineForm.value.website || undefined,
      no_of_employees: newPipelineForm.value.no_of_employees || undefined,
      lead: newPipelineForm.value.lead || undefined,
      lead_name: newPipelineForm.value.lead_name || undefined
    }

    // Remove undefined values
    Object.keys(docData).forEach(key => {
      if (docData[key] === undefined) {
        delete docData[key]
      }
    })

    const result = await call('frappe.client.insert', {
      doc: docData
    })
    
    toast.success('Pipeline created successfully')
    showPipelineModal.value = false
    
    // Reset form
    newPipelineForm.value = {
      pipeline_name: '',
      status: 'Open',
      organization: '',
      pipeline_owner: '',
      source: '',
      territory: '',
      mobile_no: '',
      est_pipeline_value: '',
      currency: 'USD',
      exchange_rate: '1.0',
      total_deal_value: '',
      website: '',
      no_of_employees: '',
      lead: '',
      lead_name: ''
    }
    
    // Reset to first tab
    activeTab.value = 'basic'
    
    // Refresh the list
    await fetchPipelines()
    
  } catch (error) {
    console.error('Error creating pipeline:', error)
    toast.error('Failed to create pipeline')
  } finally {
    creatingPipeline.value = false
  }
}

// Search with debounce
let searchTimeout = null
function debouncedSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    fetchPipelines()
  }, 500)
}

// Pagination methods
function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    fetchPipelines()
  }
}

function previousPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    fetchPipelines()
  }
}

function goToPage(page) {
  currentPage.value = page
  fetchPipelines()
}

// Navigation
function viewPipeline(pipelineId) {
  router.push({
    name: 'Pipeline',
    params: { pipelineId: pipelineId }
  })
}

function openPipelineActions(pipeline) {
  // Implement pipeline actions (edit, delete, etc.)
  console.log('Pipeline actions:', pipeline)
}

// Helper functions
function getInitials(name) {
  if (!name) return '—'
  return name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)
}

function getShortName(fullName) {
  if (!fullName) return '—'
  const names = fullName.split(' ')
  return names.length > 1 ? `${names[0]} ${names[1][0]}.` : names[0]
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

function isLiked(likedBy) {
  if (!likedBy) return false
  try {
    const likedArray = JSON.parse(likedBy)
    return likedArray && likedArray.length > 0
  } catch {
    return false
  }
}

// Lifecycle
onMounted(() => {
  fetchPipelineStatuses()
  fetchPipelines()
})
</script>

<style scoped>
/* Custom styles */
.hover\:bg-blue-50:hover {
  background-color: #eff6ff;
}

.transition-colors {
  transition: all 0.15s ease-in-out;
}

.transition-all {
  transition: all 0.15s ease-in-out;
}

/* Sticky header styles */
.sticky {
  position: sticky;
  z-index: 10;
}
</style>
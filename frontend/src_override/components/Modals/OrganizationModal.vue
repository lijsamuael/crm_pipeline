<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body>
      <div class="px-4 pt-5 pb-6 bg-surface-modal sm:px-6">
        <div class="flex items-center justify-between mb-5">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('New Organization') }}
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
        <FieldLayout
          v-if="tabs.data?.length"
          :tabs="tabs.data"
          :data="organization.doc"
          doctype="CRM Organization"
        />
        <div v-if="isMalaysia" class="mt-4 flex flex-col gap-3">
          <FormControl
            type="select"
            :label="__('State')"
            v-model="organization.doc._malaysia_state"
            :options="malaysiaStateOptions"
          />
          <FormControl
            type="text"
            :label="__('City')"
            v-model="organization.doc._malaysia_city"
            :placeholder="__('e.g. Kuala Lumpur')"
          />
        </div>
        <ErrorMessage class="mt-8" v-if="error" :message="__(error)" />
      </div>
      <div class="px-4 pt-4 pb-7 sm:px-6">
        <div class="space-y-2">
          <Button
            class="w-full"
            variant="solid"
            :label="__('Create')"
            :loading="loading"
            @click="createOrganization"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import { usersStore } from '@/stores/users'
import { isMobileView } from '@/composables/settings'
import {
  showQuickEntryModal,
  quickEntryProps,
  showAddressModal,
  addressProps,
} from '@/composables/modals'
import { useDocument } from '@/data/document'
import { capture } from '@/telemetry'
import { call, FeatherIcon, createResource } from 'frappe-ui'
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({}),
  },
  options: {
    type: Object,
    default: {
      redirect: true,
      afterInsert: () => {},
    },
  },
})

const { isManager } = usersStore()

const router = useRouter()
const show = defineModel()

const loading = ref(false)
const error = ref(null)

const { document: organization, triggerOnBeforeCreate } =
  useDocument('CRM Organization')

const MALAYSIA_STATES = [
  'Johor', 'Kedah', 'Kelantan', 'Melaka', 'Negeri Sembilan',
  'Pahang', 'Pulau Pinang', 'Perak', 'Perlis', 'Selangor',
  'Terengganu', 'Sabah', 'Sarawak',
  'Wilayah Persekutuan Kuala Lumpur',
  'Wilayah Persekutuan Labuan',
  'Wilayah Persekutuan Putrajaya',
  'Not Applicable'
]

const malaysiaStateOptions = MALAYSIA_STATES.map(s => ({ label: s, value: s }))

const siteDefaultCountry = ref('')
call('fr8labs_custom_crm.fr8labs_custom_crm.sync_customer_fr8labs.app_utils.get_site_default_country').then((r) => {
  siteDefaultCountry.value = r || ''
})

const isMalaysia = computed(() => {
  return siteDefaultCountry.value === 'Malaysia' && organization.doc?.custom_country === 'Malaysia'
})

async function createOrganization() {
  loading.value = true
  error.value = null

  if (isMalaysia.value) {
    if (!organization.doc._malaysia_state) {
      organization.doc._malaysia_state = 'Not Applicable'
    }
    if (!(organization.doc._malaysia_city || '').trim()) {
      error.value = 'City is required for Malaysian organizations'
      loading.value = false
      return
    }
  }

  await triggerOnBeforeCreate?.()

  const doc = await call(
    'frappe.client.insert',
    {
      doc: {
        doctype: 'CRM Organization',
        ...organization.doc,
      },
    },
    {
      onError: (err) => {
        if (err.error.exc_type == 'ValidationError') {
          error.value = err.error?.messages?.[0]
          loading.value = false
        }
      },
    },
  )
  loading.value = false
  if (doc.name) {
    capture('organization_created')
    handleOrganizationUpdate(doc)
  }
}

function handleOrganizationUpdate(doc) {
  if (doc.name && props.options.redirect) {
    router.push({
      name: 'Organization',
      params: { organizationId: doc.name },
    })
  }
  show.value = false
  props.options.afterInsert && props.options.afterInsert(doc)
}

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Organization'],
  params: { doctype: 'CRM Organization', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    return _tabs.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          column.fields.forEach((field) => {
            if (field.fieldname == 'address') {
              field.create = (value, close) => {
                organization.doc.address = value
                openAddressModal()
                close()
              }
              field.edit = (address) => openAddressModal(address)
            } else if (field.fieldtype === 'Table') {
              organization.doc[field.fieldname] = []
            }
          })
        })
      })
    })
  },
})

onMounted(() => {
  organization.doc = { no_of_employees: '1-10' }
  Object.assign(organization.doc, props.data)
})

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'CRM Organization' }
  nextTick(() => (show.value = false))
}

function openAddressModal(_address) {
  showAddressModal.value = true
  addressProps.value = {
    doctype: 'Address',
    address: _address,
  }
}
</script>

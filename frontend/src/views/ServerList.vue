<script setup lang="ts">
import { ref, onMounted } from "vue"
import apiClient from "../api/client"

interface Server {
  id: string
  name: string
  ip_address: string
  ssh_user: string
  is_active?: boolean
}

const servers = ref<Server[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const isModalOpen = ref(false)
const adding = ref(false)
const addError = ref<string | null>(null)
const newServerForm = ref({ name: "", ip_address: "", ssh_user: "root", initial_password: "" })

// Details modal state
const isDetailsOpen = ref(false)
const currentServer = ref<Server | null>(null)
const detailsError = ref<string | null>(null)
const bootstrapping = ref(false)
const deleting = ref(false)
// After-add bootstrap state
const isBootstrappingAfterAdd = ref(false)
const bootLogsAfterAdd = ref<string | null>(null)
const bootErrorAfterAdd = ref<string | null>(null)
const bootSuccessAfterAdd = ref(false)

const fetchServers = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await apiClient.get("/servers/")
    servers.value = response.data
  } catch (err: any) {
    error.value = err.message || "Failed to fetch servers"
  } finally {
    loading.value = false
  }
}

const openModal = () => {
  addError.value = null
  newServerForm.value = { name: "", ip_address: "", ssh_user: "root", initial_password: "" }
  isModalOpen.value = true
}

const closeModal = () => {
  isModalOpen.value = false
}

const openDetails = (server: Server) => {
  detailsError.value = null
  currentServer.value = server
  isDetailsOpen.value = true
}

const closeDetails = () => {
  isDetailsOpen.value = false
  currentServer.value = null
}

const bootstrapServer = async () => {
  if (!currentServer.value) return
  bootstrapping.value = true
  detailsError.value = null
  try {
    await apiClient.post(`/servers/${currentServer.value.id}/bootstrap`)
    // Optionally inform user; here we just refresh list
    await fetchServers()
  } catch (err: any) {
    detailsError.value = err.response?.data?.detail || err.message || 'Bootstrap failed'
  } finally {
    bootstrapping.value = false
  }
}

const deleteServer = async () => {
  if (!currentServer.value) return
  deleting.value = true
  detailsError.value = null
  try {
    await apiClient.delete(`/servers/${currentServer.value.id}`)
    // remove from local list
    servers.value = servers.value.filter(s => s.id !== currentServer.value!.id)
    closeDetails()
  } catch (err: any) {
    detailsError.value = err.response?.data?.detail || err.message || 'Delete failed'
  } finally {
    deleting.value = false
  }
}

const addServer = async () => {
  adding.value = true
  addError.value = null
  try {
    const response = await apiClient.post("/servers/", newServerForm.value)
    // Add to list and start bootstrap flow inside modal
    servers.value.push(response.data)
    // Keep modal open and start bootstrapping
    currentServer.value = response.data
    isBootstrappingAfterAdd.value = true
    bootLogsAfterAdd.value = null
    bootErrorAfterAdd.value = null
    await runBootstrapAfterAdd(response.data.id)
  } catch (err: any) {
    addError.value = err.response?.data?.detail || err.message || "Failed to add server"
  } finally {
    adding.value = false
  }
}

const runBootstrapAfterAdd = async (serverId: string) => {
  bootstrapping.value = true
  bootLogsAfterAdd.value = null
  bootErrorAfterAdd.value = null
  try {
    const res = await apiClient.post(`/servers/${serverId}/bootstrap`)
    // success -> show message and refresh servers
    bootLogsAfterAdd.value = res.data?.details || res.data?.message || 'Bootstrap finished'
    // refresh list to get updated state
    await fetchServers()
    // mark success; user will close modal manually
    bootSuccessAfterAdd.value = true
  } catch (err: any) {
    bootErrorAfterAdd.value = err.response?.data?.detail || err.message || 'Bootstrap failed'
    // If backend returned details, include them
    try {
      bootLogsAfterAdd.value = err.response?.data?.details || String(err)
    } catch {
      bootLogsAfterAdd.value = String(err)
    }
  } finally {
    bootstrapping.value = false
  }
}

const retryAfterAdd = async () => {
  if (!currentServer.value) return
  bootErrorAfterAdd.value = null
  bootLogsAfterAdd.value = null
  bootSuccessAfterAdd.value = false
  isBootstrappingAfterAdd.value = true
  await runBootstrapAfterAdd(currentServer.value.id)
}

const closeAfterAdd = () => {
  isBootstrappingAfterAdd.value = false
  bootSuccessAfterAdd.value = false
  bootLogsAfterAdd.value = null
  bootErrorAfterAdd.value = null
  closeModal()
}

onMounted(() => {
  fetchServers()
})
</script>

<template>
  <div>
    <div class="sm:flex sm:items-center">
      <div class="sm:flex-auto">
        <h1 class="text-base font-semibold leading-6 text-gray-900">Servers</h1>
        <p class="mt-2 text-sm text-gray-700">A list of all connecteb servers.</p>
      </div>
      <div class="mt-4 sm:ml-16 sm:mt-0 sm:flex-none">
        <button @click="openModal" type="button" class="block rounded-md bg-indigo-600 px-3 py-2 text-center text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">Add server</button>
      </div>
    </div>
    <div class="mt-8 flow-root">
      <div class="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
        <div class="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
          <div class="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
            
            <div v-if="loading" class="p-4 text-center text-gray-500">Loading...</div>
            <div v-else-if="error" class="p-4 text-center text-red-500">{{ error }}</div>
            <table v-else class="min-w-full divide-y divide-gray-300">
              <thead class="bg-gray-50">
                <tr>
                  <th scope="col" class="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">Name</th>
                  <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">IP Address</th>
                  <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">User</th>
                  <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Status</th>
                  <th scope="col" class="relative py-3.5 pl-3 pr-4 sm:pr-6">
                    <span class="sr-only">Edit</span>
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 bg-white">
                <tr v-for="server in servers" :key="server.id">
                  <td class="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">{{ server.name }}</td>
                  <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{{ server.ip_address }}</td>
                  <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{{ server.ssh_user }}</td>
                  <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                    <span v-if="server.is_active === true" class="inline-flex items-center rounded-md bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20">Active</span>
                    <span v-else-if="server.is_active === false" class="inline-flex items-center rounded-md bg-red-50 px-2 py-1 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/10">Offline</span>
                    <span v-else class="inline-flex items-center rounded-md bg-gray-50 px-2 py-1 text-xs font-medium text-gray-700 ring-1 ring-inset ring-gray-600/10">Unknown</span>
                  </td>
                  <td class="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                    <button @click="openDetails(server)" class="text-indigo-600 hover:text-indigo-900">Details<span class="sr-only">, {{ server.name }}</span></button>
                  </td>
                </tr>
                <tr v-if="servers.length === 0">
                  <td colspan="5" class="px-3 py-4 text-center text-sm text-gray-500">No servers found.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Server Modal -->
    <div v-if="isModalOpen" class="relative z-10" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
      <div class="fixed inset-0 z-10 w-screen overflow-y-auto">
        <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
          <div class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
            <div class="absolute right-0 top-0 hidden pr-4 pt-4 sm:block">
              <button @click="closeModal" type="button" class="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2">
                <span class="sr-only">Close</span>
                <span class="text-2xl">&times;</span>
              </button>
            </div>
            <div class="sm:flex sm:items-start">
              <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
                <h3 class="text-base font-semibold leading-6 text-gray-900" id="modal-title">Add New Server</h3>
                <div class="mt-4">
                  <template v-if="!isBootstrappingAfterAdd">
                    <form @submit.prevent="addServer" class="space-y-4">
                    <div>
                      <label for="name" class="block text-sm font-medium leading-6 text-gray-900">Server Name (e.g. prod-1)</label>
                      <div class="mt-2">
                        <input type="text" v-model="newServerForm.name" id="name" required class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 pl-2" placeholder="My production server">
                      </div>
                    </div>
                    <div>
                      <label for="initial_password" class="block text-sm font-medium leading-6 text-gray-900">Initial SSH Password (optional)</label>
                      <div class="mt-2">
                        <input type="password" v-model="newServerForm.initial_password" id="initial_password" class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 pl-2" placeholder="Leave empty to use existing key">
                      </div>
                    </div>
                    <div>
                      <label for="ip_address" class="block text-sm font-medium leading-6 text-gray-900">IP Address (IPv4)</label>
                      <div class="mt-2">
                        <input type="text" v-model="newServerForm.ip_address" id="ip_address" required class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 pl-2" placeholder="192.168.1.100">
                      </div>
                    </div>
                    <div>
                      <label for="ssh_user" class="block text-sm font-medium leading-6 text-gray-900">SSH User</label>
                      <div class="mt-2">
                        <input type="text" v-model="newServerForm.ssh_user" id="ssh_user" required class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 pl-2" placeholder="root">
                      </div>
                    </div>
                    
                    <div v-if="addError" class="text-sm text-red-600 mt-2">{{ addError }}</div>

                    <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                      <button type="submit" :disabled="adding" class="inline-flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 sm:ml-3 sm:w-auto disabled:opacity-50">
                        {{ adding ? "Adding..." : "Add Server" }}
                      </button>
                      <button @click="closeModal" type="button" class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto">Cancel</button>
                    </div>
                  </form>
                  </template>

                  <template v-else>
                    <div class="space-y-4">
                      <div class="text-sm text-gray-700">Bootstrapping server <strong>{{ currentServer?.name }}</strong> — this may take a minute.</div>
                      <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                        <div class="h-2 bg-indigo-600 animate-pulse" style="width:100%"></div>
                      </div>
                        <div v-if="bootstrapping" class="text-sm text-gray-500">Running bootstrap...</div>
                      <div v-else>
                        <div v-if="bootSuccessAfterAdd" class="text-sm text-green-600">Bootstrap completed successfully.</div>
                        <div v-if="bootErrorAfterAdd" class="text-sm text-red-600">Bootstrap failed: {{ bootErrorAfterAdd }}</div>
                        <div v-if="bootLogsAfterAdd" class="mt-2">
                          <label class="block text-sm font-medium text-gray-700">Logs</label>
                          <pre class="mt-1 max-h-48 overflow-auto rounded bg-gray-50 p-2 text-xs text-gray-800">{{ bootLogsAfterAdd }}</pre>
                        </div>
                        <div class="mt-4 sm:flex sm:flex-row-reverse">
                          <button v-if="bootErrorAfterAdd" @click="retryAfterAdd" class="inline-flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 sm:ml-3 sm:w-auto">Retry</button>
                          <button @click="closeAfterAdd" class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto">Close</button>
                        </div>
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Server Details Modal -->
    <div v-if="isDetailsOpen" class="relative z-10" aria-labelledby="details-title" role="dialog" aria-modal="true">
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
      <div class="fixed inset-0 z-10 w-screen overflow-y-auto">
        <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
          <div class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
            <div class="absolute right-0 top-0 hidden pr-4 pt-4 sm:block">
              <button @click="closeDetails" type="button" class="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2">
                <span class="sr-only">Close</span>
                <span class="text-2xl">&times;</span>
              </button>
            </div>
            <div class="sm:flex sm:items-start">
              <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
                <h3 class="text-base font-semibold leading-6 text-gray-900" id="details-title">Server Details</h3>
                <div class="mt-4">
                  <div v-if="detailsError" class="text-sm text-red-600">{{ detailsError }}</div>
                  <div v-if="currentServer">
                    <p class="text-sm"><strong>Name:</strong> {{ currentServer.name }}</p>
                    <p class="text-sm"><strong>IP:</strong> {{ currentServer.ip_address }}</p>
                    <p class="text-sm"><strong>User:</strong> {{ currentServer.ssh_user }}</p>
                  </div>
                </div>

                <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                  <button @click="bootstrapServer" :disabled="bootstrapping" class="inline-flex w-full justify-center rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-500 sm:ml-3 sm:w-auto disabled:opacity-50">{{ bootstrapping ? 'Running...' : 'Bootstrap' }}</button>
                  <button @click="deleteServer" :disabled="deleting" class="mt-3 inline-flex w-full justify-center rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 sm:mt-0 sm:w-auto disabled:opacity-50">{{ deleting ? 'Deleting...' : 'Delete' }}</button>
                  <button @click="closeDetails" type="button" class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto">Close</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from "vue"
import apiClient from "../api/client"

interface Project {
  id: string
  name: string
  image: string
  domain: string
  status: string
  server_id: string
}

interface Server {
  id: string
  name: string
}

const projects = ref<Project[]>([])
const servers = ref<Server[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const isModalOpen = ref(false)
const deploying = ref(false)
const deployError = ref<string | null>(null)
const newProjectForm = ref({ name: "", image: "", domain: "", server_id: "" })

const fetchProjects = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await apiClient.get("/projects/")
    projects.value = response.data
  } catch (err: any) {
    error.value = err.message || "Failed to fetch projects"
  } finally {
    loading.value = false
  }
}

const fetchServers = async () => {
  try {
    const response = await apiClient.get("/servers/")
    servers.value = response.data
  } catch (err) {
    console.error("Failed to fetch servers for dropdown:", err)
  }
}

const openModal = async () => {
  deployError.value = null
  newProjectForm.value = { name: "", image: "", domain: "", server_id: "" }
  await fetchServers()
  isModalOpen.value = true
}

const closeModal = () => {
  isModalOpen.value = false
}

const deployProject = async () => {
  deploying.value = true
  deployError.value = null
  try {
    const response = await apiClient.post("/projects/", newProjectForm.value)
    projects.value.push(response.data)
    closeModal()
  } catch (err: any) {
    deployError.value = err.response?.data?.detail || err.message || "Failed to deploy project"
  } finally {
    deploying.value = false
  }
}

const deleteProject = async (id: string, name: string) => {
  if (!confirm(`Are you sure you want to delete ${name}?`)) return;
  try {
    await apiClient.delete(`/projects/${id}`)
    projects.value = projects.value.filter(p => p.id !== id)
  } catch (err: any) {
    alert("Failed to delete project: " + err.message)
  }
}

onMounted(() => {
  fetchProjects()
})
</script>

<template>
  <div>
    <div class="sm:flex sm:items-center">
      <div class="sm:flex-auto">
        <h1 class="text-base font-semibold leading-6 text-gray-900">Projects</h1>
        <p class="mt-2 text-sm text-gray-700">A list of all deployed projects.</p>
      </div>
      <div class="mt-4 sm:ml-16 sm:mt-0 sm:flex-none">
        <button @click="openModal" type="button" class="block rounded-md bg-indigo-600 px-3 py-2 text-center text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">Deploy Project</button>
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
                  <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Image</th>
                  <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Domain</th>
                  <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Status</th>
                  <th scope="col" class="relative py-3.5 pl-3 pr-4 sm:pr-6">
                    <span class="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 bg-white">
                <tr v-for="project in projects" :key="project.id">
                  <td class="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">{{ project.name }}</td>
                  <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{{ project.image }}</td>
                  <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{{ project.domain }}</td>
                  <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                    <span class="inline-flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-600/20">{{ project.status }}</span>
                  </td>
                  <td class="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                    <a href="#" @click.prevent="deleteProject(project.id, project.name)" class="text-red-600 hover:text-red-900">Delete</a>
                  </td>
                </tr>
                <tr v-if="projects.length === 0">
                  <td colspan="5" class="px-3 py-4 text-center text-sm text-gray-500">No projects found.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Deploy Project Modal -->
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
                <h3 class="text-base font-semibold leading-6 text-gray-900" id="modal-title">Deploy New Project</h3>
                <div class="mt-4">
                  <form @submit.prevent="deployProject" class="space-y-4">
                    <div>
                      <label for="p_name" class="block text-sm font-medium leading-6 text-gray-900">Project Name</label>
                      <div class="mt-2">
                        <input type="text" v-model="newProjectForm.name" id="p_name" required class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 pl-2" placeholder="my-app">
                      </div>
                    </div>
                    <div>
                      <label for="p_image" class="block text-sm font-medium leading-6 text-gray-900">Docker Image</label>
                      <div class="mt-2">
                        <input type="text" v-model="newProjectForm.image" id="p_image" required class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 pl-2" placeholder="nginx:latest">
                      </div>
                    </div>
                    <div>
                      <label for="p_domain" class="block text-sm font-medium leading-6 text-gray-900">Domain / Route</label>
                      <div class="mt-2">
                        <input type="text" v-model="newProjectForm.domain" id="p_domain" required class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 pl-2" placeholder="app.example.com">
                      </div>
                    </div>
                    <div>
                      <label for="p_server" class="block text-sm font-medium leading-6 text-gray-900">Target Server</label>
                      <div class="mt-2">
                        <select v-model="newProjectForm.server_id" id="p_server" required class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 pl-2">
                          <option disabled value="">Please select a server</option>
                          <option v-for="s in servers" :key="s.id" :value="s.id">{{ s.name }}</option>
                        </select>
                      </div>
                    </div>
                    
                    <div v-if="deployError" class="text-sm text-red-600 mt-2">{{ deployError }}</div>

                    <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                      <button type="submit" :disabled="deploying" class="inline-flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 sm:ml-3 sm:w-auto disabled:opacity-50">
                        {{ deploying ? "Deploying..." : "Deploy" }}
                      </button>
                      <button @click="closeModal" type="button" class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto">Cancel</button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
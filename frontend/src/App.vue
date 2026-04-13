<script setup lang="ts">
import { RouterView, RouterLink } from 'vue-router'
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-indigo-600 shadow">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="flex h-16 justify-between">
          <div class="flex">
            <div class="flex flex-shrink-0 items-center">
              <span class="text-white text-xl font-bold">Deplock</span>
            </div>
            <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
              <RouterLink to="/servers" class="inline-flex items-center border-b-2 border-transparent px-1 pt-1 text-sm font-medium text-indigo-100 hover:border-indigo-300 hover:text-white" active-class="!border-white !text-white">Servers</RouterLink>
              <RouterLink to="/projects" class="inline-flex items-center border-b-2 border-transparent px-1 pt-1 text-sm font-medium text-indigo-100 hover:border-indigo-300 hover:text-white" active-class="!border-white !text-white">Projects</RouterLink>
            </div>
          </div>
        </div>
      </div>
    </nav>

    <main>
      <div class="mx-auto max-w-7xl py-6 sm:px-6 lg:px-8">
        <RouterView />
      </div>
    </main>
  </div>
</template>

import { createRouter, createWebHistory } from 'vue-router'
import ServerList from '../views/ServerList.vue'
import ProjectList from '../views/ProjectList.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/servers'
    },
    {
      path: '/servers',
      name: 'servers',
      component: ServerList
    },
    {
      path: '/projects',
      name: 'projects',
      component: ProjectList
    }
  ]
})

export default router

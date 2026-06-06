<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth.js'

const router = useRouter()
const auth = useAuthStore()

onMounted(async () => {
  const restored = await auth.tryRestoreSession()
  if (!restored) {
    router.push({ name: 'login' })
  }
})
</script>

<template>
  <router-view />
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

// Existing setup code
defineProps({
  msg: String,
})

const count = ref(0)

// New setup code for routing
const router = useRouter();

const navigateToPractice = () => {
  const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true'; // Or your actual logic for checking auth state
  if (isAuthenticated) {
    // User is authenticated, navigate to Chatbot
    router.push({ name: 'Chatbot' });
  } else {
    // User is not authenticated, navigate to Login
    router.push({ name: 'Login' });
  }
};
</script>

<template>
  <h1>{{ msg }}</h1>

  <div class="card">
    <button type="button" @click="count++">count is {{ count }}</button>
    <p>
      Edit
      <code>components/HelloWorld.vue</code> to test HMR
    </p>
  </div>

  <!-- Practice Now! button -->
  <button @click="navigateToPractice">Practice Now!</button>

  <p>
    Check out
    <a href="https://vuejs.org/guide/quick-start.html#local" target="_blank">create-vue</a>,
    the official Vue + Vite starter
  </p>
  <p>
    Install
    <a href="https://github.com/vuejs/language-tools" target="_blank">Volar</a>
    in your IDE for a better DX
  </p>
  <p class="read-the-docs">Click on the Vite and Vue logos to learn more</p>
</template>

<style scoped>
.read-the-docs {
  color: #888;
}
</style>

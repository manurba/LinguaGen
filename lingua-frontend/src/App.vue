<script setup>
import HomePage from './components/HomePage.vue'
import GoogleLoginButton from './components/GoogleLoginButton.vue';
import LogoutButton from './components/LogoutButton.vue';
import { authState } from './authState';
</script>

<template>
  <div class="container">
    <div class="content">
      <a href="https://linguagen.tech" target="_blank">
        <img src="/LinguaGen_Logo-removebg.png" class="logo" alt="LinguaGen logo" />
      </a>
    </div>
    <div id="app">
      <router-view></router-view>
    </div>
  </div>
</template>

<style>
/* Remove the global overflow: hidden from here if it exists */
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
}
</style>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  margin: 0;
  padding: 0;
  overflow: hidden;
  position: fixed;
  width: 100%;
  top: 0;
  left: 0;
  background-color: #fff;
}

/* Add this route-specific styling */
:deep(.chatbot-route) {
  overflow: hidden;
  background-color: #fff;
  height: 100%;
  width: 100%;
}

.content {
  flex-shrink: 0;
  background-color: #fff;
}

#app {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  width: 60%; /* Add this */
  max-width: none; /* Add this */
}

.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}

</style>

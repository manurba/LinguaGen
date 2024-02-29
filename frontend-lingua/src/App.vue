<script setup>
import HelloWorld from './components/HelloWorld.vue'
import GoogleLoginButton from './components/GoogleLoginButton.vue';
import { authState } from './authState';
</script>

<template>
  <div class="container">
    <div class="content">
      <a href="https://vitejs.dev" target="_blank">
        <img src="/vite.svg" class="logo" alt="Vite logo" />
      </a>
      <a href="https://vuejs.org/" target="_blank">
        <img src="./assets/vue.svg" class="logo vue" alt="Vue logo" />
      </a>
    </div>
    <!-- <div class="login-button" v-if="!authState.isAuthenticated">
      <GoogleLoginButton />
    </div> -->
    <div id="app">
    <router-view></router-view> <!-- This line is crucial -->
  </div>
  </div>
</template>

<style scoped>
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

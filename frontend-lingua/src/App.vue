<script setup>
import HelloWorld from './components/HelloWorld.vue'
import GoogleLoginButton from './components/GoogleLoginButton.vue';
import { authState } from './authState';
</script>

<template>
  <div class="container">
    <div class="content">
      <!-- Update the href if needed to point to your website or remove the <a> tag if not required -->
      <a href="http://localhost:3000" target="_blank">
        <!-- Update the src attribute to the path of your new logo file -->
        <img src="/LinguaGen_Logo-removebg.png" class="logo" alt="LinguaGen logo" />
      </a>
    </div>
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

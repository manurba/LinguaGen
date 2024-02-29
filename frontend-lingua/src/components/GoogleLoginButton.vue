<template>
  <GoogleLogin :client-id="yourGoogleClientID" :callback="callback"/>
</template>

<script setup>
import { GoogleLogin } from 'vue3-google-login';
import { useRouter } from 'vue-router';
import { authState } from '../authState';

const yourGoogleClientID = import.meta.env.VITE_GOOGLE_CLIENT_ID; // Replace this with your actual client ID
const router = useRouter();

const callback = (response) => {
  console.log("Handle the response", response);
  if (response && !response.error) { // Simple check, adjust based on actual response structure
    localStorage.setItem('isAuthenticated', 'true');
    authState.isAuthenticated = true;
    router.push({ name: 'chatbot' });
  } else {
    // Handle login failure
    console.error('Login failed:', response.error);
  }
};
</script>

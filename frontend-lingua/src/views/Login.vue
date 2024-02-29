<template>
    <div class="login-container">
        <div class="login-box">
        <GoogleLoginButton />
        </div>
    </div>
</template>

<script setup>
import GoogleLoginButton from '../components/GoogleLoginButton.vue';
</script>

<style scoped>
.login-container {
display: flex;
justify-content: center;
align-items: center;
height: 100vh; /* Full viewport height */
background-color: #f5f5f5; /* Light gray background */
}

.login-box {
padding: 20px;
border-radius: 8px;
box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); /* Soft shadow for the box */
background-color: white; /* White background for the box */
}
</style>

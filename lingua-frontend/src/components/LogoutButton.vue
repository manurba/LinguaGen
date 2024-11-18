<template>
  <button @click="handleLogout" class="logout-btn">
    <i class="fas fa-sign-out-alt"></i>
    Logout
  </button>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { logout } from '../utils/auth';
import { authState } from '../authState';

const router = useRouter();

const handleLogout = () => {
  logout();
  authState.setAuthenticated(false);
  router.push({ name: 'Home' });
};
</script>

<style scoped>
.logout-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.8rem;
  border: none;
  border-radius: 4px;
  background-color: #f44336;
  color: white;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.logout-btn:hover {
  background-color: #d32f2f;
}

.logout-btn i {
  font-size: 0.9rem;
}
</style>

<template>
  <div class="chat-container">
    <div class="messages-container">
      <div v-for="(message, index) in messages" :key="index" class="message" :class="{ 'user-message': message.isUser, 'bot-message': !message.isUser }">
        {{ message.text }}
      </div>
    </div>
    <div class="input-container">
      <input v-model="userInput" @keyup.enter="sendMessage" placeholder="Type a message..." type="text" />
      <button v-if="authState.isAuthenticated" @click="sendMessage">Send</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { authState } from '../authState';
console.log(authState.isAuthenticated)
const messages = ref([]);
const userInput = ref('');

const sendMessage = () => {
  if (userInput.value.trim() !== '') {
    // Add user message to messages array
    messages.value.push({ text: userInput.value, isUser: true });
    userInput.value = ''; // Clear input field

    // Simulate bot response
    setTimeout(() => {
      messages.value.push({ text: 'This is a simulated response.', isUser: false });
    }, 1000);
  }
};
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 90vh;
  max-width: 600px;
  margin: auto;
  border: 1px solid #ccc;
  border-radius: 8px;
  overflow: hidden;
}

.messages-container {
  flex-grow: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #f5f5f5;
}

.message {
  margin-bottom: 12px;
  padding: 10px;
  border-radius: 20px;
  color: white;
  max-width: 75%;
}

.user-message {
  background-color: #007bff;
  align-self: flex-end;
}

.bot-message {
  background-color: #666;
  align-self: flex-start;
}

.input-container {
  display: flex;
  padding: 10px;
  background-color: #fff;
  border-top: 1px solid #ccc;
}

.input-container input {
  flex-grow: 1;
  margin-right: 10px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 20px;
}

.input-container button {
  padding: 10px 20px;
  border: none;
  border-radius: 20px;
  background-color: #007bff;
  color: white;
  cursor: pointer;
}
</style>

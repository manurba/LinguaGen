<template>
  <div class="chat-container">
    <div class="messages-container">
      <div v-for="(message, index) in messages" :key="index"
           class="message" :class="{ 'user-message': message.isUser,
                                      'bot-message': !message.isUser,
                                      'audio-message': message.isAudio }">
        <template v-if="message.isAudio">
          <div class="audio-player">
            <audio :src="message.audioSrc" controls></audio>
          </div>
        </template>
        <template v-else>
          <div class="text-message">{{ message.text }}</div>
        </template>
      </div>
    </div>
    <div class="input-container">
      <input v-model="userInput" @keyup.enter="sendMessage" placeholder="Type a message..." type="text" :disabled="isRecording" />
      <button v-if="authState.isAuthenticated && !isRecording && !isProcessing" @click="sendMessage" :disabled="isProcessing || isRecording">Send</button>
      <button v-if="!isRecording" @click="startRecording" :disabled="isProcessing">Record</button>
      <button v-else @click="stopRecording" :disabled="isProcessing">Stop</button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import { authState } from '../authState';

const messages = ref([]);
const userInput = ref('');
const isRecording = ref(false);
const audioChunks = ref([]);
const conversationId = ref('');
const isProcessing = ref(false);
let mediaRecorder;

// Function to scroll the conversation to the bottom
async function scrollToBottom() {
  await nextTick();
  const container = document.querySelector(".messages-container");
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
}

// Fetch a new conversation ID from the server
async function fetchConversationId() {
  try {
    const response = await fetch('http://localhost:5000/new_conversation');
    const data = await response.json();
    conversationId.value = data.conversation_id;
  } catch (error) {
    console.error('Error fetching new conversation ID:', error);
  }
}

// Call fetchConversationId immediately to ensure a conversation ID is available as soon as possible
fetchConversationId();

async function sendMessage() {
  const trimmedInput = userInput.value.trim();
  if (trimmedInput && !isProcessing.value) {
    isProcessing.value = true;
    messages.value.push({ text: trimmedInput, isUser: true, isAudio: false });
    userInput.value = ''; // Clear input field immediately after use

    const formData = new FormData();
    formData.append('conversation_id', conversationId.value);
    formData.append('text_input', trimmedInput);

    scrollToBottom(); // Scroll to bottom after sending a message
    await sendToServer(formData);
  }
}

async function sendToServer(formData) {
  try {
    const response = await fetch('http://localhost:5000/get_response', { method: 'POST', body: formData });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    handleServerResponse(data);
  } catch (error) {
    console.error('Error communicating with server:', error);
  }
}

function handleServerResponse(data) {
  // Handle text responses
  if (data.conversation) {
    const botResponse = data.conversation[data.conversation.length - 1];
    if (botResponse && botResponse.role === 'assistant') {
      messages.value.push({ text: botResponse.content, isUser: false, isAudio: false });
    }
  }

  // Handle audio responses
  if (data.file) {
    const audioResponseUrl = `http://localhost:5000/${data.file}`;
    messages.value.push({ audioSrc: audioResponseUrl, isUser: false, isAudio: true });

    nextTick().then(playLastAudio);
  }
  scrollToBottom(); // Scroll to bottom after sending a message
}

function playLastAudio() {
  const audioElements = document.querySelectorAll('audio');
  const lastAudioElement = audioElements[audioElements.length - 1];
  if (lastAudioElement) {
    lastAudioElement.play().catch(error => console.error('Error playing audio:', error));
    lastAudioElement.onended = () => {
      isProcessing.value = false;
    };
  }
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();
    isRecording.value = true;
    audioChunks.value = [];

    mediaRecorder.ondataavailable = event => {
      audioChunks.value.push(event.data);
    };
  } catch (error) {
    console.error('Error starting recording:', error);
  }
}

async function stopRecording() {
  mediaRecorder.stop();
  isRecording.value = false;

  mediaRecorder.onstop = async () => {
    isProcessing.value = true; // Start processing
    if (!conversationId.value) {
      await fetchConversationId();
      if (!conversationId.value) {
        console.error('Failed to retrieve conversation ID.');
        isProcessing.value = false; // Ensure processing is ended in case of failure
        return;
      }
    }

    const audioBlob = new Blob(audioChunks.value, { type: 'audio/wav' });
    messages.value.push({ audioSrc: URL.createObjectURL(audioBlob), isUser: true, isAudio: true });

    const formData = new FormData();
    formData.append('file', audioBlob);
    formData.append('conversation_id', conversationId.value);

    await sendToServer(formData);
  };
  scrollToBottom();
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 70vh;
  width: 500px;
  margin: auto;
  border: 1px solid #ccc;
  border-radius: 8px;
  overflow: hidden;
}

.messages-container {
  flex-grow: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #fffffc; /* Lightest color for the background */
}

.message {
  word-break: break-word;
  margin-bottom: 12px;
  padding: 10px;
  border-radius: 20px;
  color: white; /* Keeping text color white */
  max-width: 70%;
}

.audio-message {
  width: 60%; /* Explicitly setting a narrower width for audio messages */
  /* Ensure the alignment of audio messages is consistent with text messages */
  text-align: center; /* Center the audio player within the container */
}

.text-message {
  word-wrap: break-word;
  text-align: left; /* Ensure text within the message box is left-aligned */
}

.user-message {
  background-color: #ffbfc4; /* User message background color */
  margin-left: auto; /* Push user messages to the right */
  align-items: flex-start; /* Align text to the top-left of the message box */
}

.bot-message {
  background-color: #c5ab9e; /* Bot message background color */
  margin-right: auto; /* Push bot messages to the left */
  align-items: flex-start; /* Align text to the top-left of the message box */
}

.input-container {
  display: flex;
  padding: 10px;
  background-color: #a9a18c; /* Darker shade for the input area */
  border-top: 1px solid #ccc;
}

.input-container input {
  flex-grow: 1;
  margin-right: 10px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 20px;
  background-color: #fffffc; /* Input background color */
  color: #000000; /* Input text color */
}

.input-container button:disabled {
  background-color: #ccc; /* Greyed out */
  cursor: not-allowed;
}

.input-container button {
  padding: 10px 20px;
  border: none;
  border-radius: 20px;
  background-color: #ffbfc4; /* Button background color */
  color: white;
  cursor: pointer;
}

.audio-player audio {
  width: 100%;
  outline: none;
}

.audio-player {
  border-radius: 20px;
  overflow: hidden;
}

/* Adjust the audio player controls to match the theme */
.audio-player audio::-webkit-media-controls-panel {
  background-color: #fad5d8;
  color: white;
}

.audio-player audio::-webkit-media-controls-play-button,
.audio-player audio::-webkit-media-controls-current-time-display,
.audio-player audio::-webkit-media-controls-time-remaining-display,
.audio-player audio::-webkit-media-controls-volume-slider,
.audio-player audio::-webkit-media-controls-mute-button,
.audio-player audio::-webkit-media-controls-fullscreen-button {
  color: white;
}

.audio-player audio::-webkit-media-controls-progress-bar,
.audio-player audio::-webkit-media-controls-timeline {
  display: none;
}
</style>

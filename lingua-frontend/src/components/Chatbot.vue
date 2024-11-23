<template>
  <div class="chat-outer-container">
    <div class="buttons-container">
      <button 
        @click="startNewConversation" 
        class="new-conversation-button"
        :disabled="isProcessing"
      >
        <i class="fas fa-plus"></i> New Chat
      </button>
      <div class="logout-container">
        <LogoutButton />
      </div>
    </div>
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
        <div class="input-wrapper">
          <textarea
            v-model="userInput"
            @keyup.enter.exact="sendMessage"
            @keydown.enter.exact.prevent
            placeholder="Type a message..."
            :disabled="isRecording"
            rows="1"
            ref="messageInput"
          ></textarea>
          <div class="button-group">
            <button
              v-if="!isRecording"
              @click="startRecording"
              :disabled="isProcessing"
              class="record-button"
              :class="{ 'pulse': !isProcessing }"
            >
              <i class="fas fa-microphone"></i>
            </button>
            <button
              v-else
              @click="stopRecording"
              :disabled="isProcessing"
              class="record-button recording"
            >
              <i class="fas fa-stop"></i>
            </button>
            <button
              v-if="hasToken"
              @click="sendMessage"
              :disabled="isProcessing || isRecording"
              class="send-button"
            >
              <i class="fas fa-paper-plane"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, computed } from 'vue';
import LogoutButton from './LogoutButton.vue';

const hasToken = computed(() => {
  return !!localStorage.getItem('google_token');
});

const apiUrl = import.meta.env.VITE_API_URL;
const messages = ref([]);
const userInput = ref('');
const isRecording = ref(false);
const audioChunks = ref([]);
const conversationId = ref('');
const isProcessing = ref(false);
let mediaRecorder;
const messageInput = ref(null);

// Function to scroll the conversation to the bottom
async function scrollToBottom() {
  await nextTick();
  const container = document.querySelector(".messages-container");
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
}

// Function to get conversation ID from URL
function getConversationIdFromUrl() {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get('c');
}

// Modify the fetchConversationId function
async function fetchConversationId(forceNew = false) {
  // Check URL for existing conversation ID first
  if (!forceNew) {
    const urlConversationId = getConversationIdFromUrl();
    if (urlConversationId) {
      conversationId.value = urlConversationId;
      await fetchMessages();
      return;
    }
  }

  try {
    const token = localStorage.getItem('google_token');
    const response = await fetch(`${apiUrl}/new_conversation`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    const data = await response.json();
    conversationId.value = data.conversation_id;
    const newUrl = `${window.location.protocol}//${window.location.host}${window.location.pathname}?c=${conversationId.value}`;
    window.history.pushState({ path: newUrl }, '', newUrl);
    await fetchMessages(); // Fetch messages when conversation ID is known
  } catch (error) {
    console.error('Error fetching new conversation ID:', error);
  }
}

// New function to fetch previous messages
async function fetchMessages() {
  try {
    const token = localStorage.getItem('google_token');
    const response = await fetch(`${apiUrl}/get_conversation?conversation_id=${conversationId.value}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (response.status === 404) {
      // Conversation not found or access denied
      // Handle by creating a new conversation
      await fetchConversationId(true);
      return;
    }

    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    if (data.messages) {
      // Map messages to the format used in messages.value
      messages.value = data.messages.map(msg => {
        if (msg.role === 'user') {
          return { text: msg.content, isUser: true, isAudio: false };
        } else if (msg.role === 'assistant') {
          // Only display text for previous assistant messages
          return { text: msg.content, isUser: false, isAudio: false };
        } else {
          return null; // Ignore other roles like 'system'
        }
      }).filter(msg => msg !== null);
      await scrollToBottom();
    }
  } catch (error) {
    console.error('Error fetching conversation messages:', error);
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
    const token = localStorage.getItem('google_token');
    const response = await fetch(`${apiUrl}/get_response`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData,
      credentials: 'include'
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    handleServerResponse(data);
  } catch (error) {
    console.error('Error communicating with server:', error);
    isProcessing.value = false; // Reset processing state on error
  }
}

function handleServerResponse(data) {
  // Handle text and audio responses
  if (data.conversation) {
    const botResponse = data.conversation[data.conversation.length - 1];
    if (botResponse && botResponse.role === 'assistant') {
      messages.value.push({ text: botResponse.content, isUser: false, isAudio: false });

      // Handle audio data if available
      if (data.audio_data) {
        const audioSrc = 'data:audio/wav;base64,' + data.audio_data;
        messages.value.push({ audioSrc: audioSrc, isUser: false, isAudio: true });
        nextTick().then(playLastAudio);
      }
    }
  }

  scrollToBottom(); // Scroll to bottom after receiving a message
}

function playLastAudio() {
  const audioElements = document.querySelectorAll('audio');
  const lastAudioElement = audioElements[audioElements.length - 1];
  if (lastAudioElement) {
    lastAudioElement.play().catch(error => console.error('Error playing audio:', error));
    lastAudioElement.onended = () => {
      isProcessing.value = false;
    };
  } else {
    isProcessing.value = false; // Ensure isProcessing is reset if no audio element is found
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

// Add this function to handle textarea auto-resize
function adjustTextareaHeight(event) {
  const textarea = event.target;
  textarea.style.height = 'auto';
  const newHeight = Math.min(textarea.scrollHeight, 100); // Max height of ~4-5 lines
  textarea.style.height = newHeight + 'px';
}

// Add watch effect for userInput
watch(userInput, () => {
  nextTick(() => {
    if (messageInput.value) {
      adjustTextareaHeight({ target: messageInput.value });
    }
  });
});

const playAudio = (message) => {
    if (message.role === 'assistant' && message.audio_file) {
        const audio = new Audio(`${import.meta.env.VITE_API_URL}/${message.audio_file}`);
        audio.play();
    }
};

const startNewConversation = async () => {
  try {
    await fetchConversationId(true); // Pass true to force new conversation
    messages.value = []; // Clear current messages
    userInput.value = ''; // Clear input field
  } catch (error) {
    console.error('Error creating new conversation:', error);
  }
};
</script>

<style scoped>
.chat-outer-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  height: calc(100vh - 17rem);
}

.buttons-container {
  width: 100%;
  max-width: 1000px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.5rem;
  position: sticky;
  top: 0;
  z-index: 1;
}

.new-conversation-button {
  background-color: #007AFF;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.2s;
}

.new-conversation-button:hover:not(:disabled) {
  background-color: #0056b3;
}

.new-conversation-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.new-conversation-button i {
  font-size: 12px;
}

.logout-container {
  margin: 0;
}

.chat-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 1000px;
  height: 100%;
  min-height: 300px;
  margin: 0 auto;
  border: none;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
  background-color: #ffffff;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.message {
  padding: 14px 18px;
  margin-bottom: 12px;
  border-radius: 16px;
  max-width: 60%;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
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
  background-color: #007AFF;
  color: white;
  margin-left: auto;
  border-bottom-right-radius: 4px;
}

.bot-message {
  background-color: #ffffff;
  color: #1e293b;
  margin-right: auto;
  border-bottom-left-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.input-container {
  padding: 1rem;
  background-color: white;
  border-top: 1px solid #eee;
  position: sticky;
  bottom: 0;
}

.input-wrapper {
  display: flex;
  align-items: flex-end; /* Align items to bottom */
  background-color: #f1f5f9;
  border-radius: 12px;
  padding: 6px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.input-wrapper textarea {
  flex-grow: 1;
  padding: 12px 16px;
  font-size: 16px;
  border: none;
  background: transparent;
  color: #1e293b;
  outline: none;
  resize: none;
  min-height: 24px;
  max-height: 100px; /* Approximately 4-5 lines */
  line-height: 1.5;
  font-family: inherit;
  margin: 0;
  overflow-y: auto;
  scrollbar-width: thin;
}

.input-wrapper textarea::placeholder {
  color: #94a3b8;
}

/* Custom scrollbar for textarea */
.input-wrapper textarea::-webkit-scrollbar {
  width: 4px;
}

.input-wrapper textarea::-webkit-scrollbar-track {
  background: transparent;
}

.input-wrapper textarea::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 2px;
}

.button-group {
  display: flex;
  gap: 8px;
  padding: 0 8px;
  align-self: flex-end;
  margin-bottom: 6px;
}

.record-button, .send-button {
  width: 42px;
  height: 42px;
  border: none;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.record-button {
  background-color: #ef4444;
  color: white;
}

.record-button:hover:not(:disabled) {
  background-color: #dc2626;
}

.record-button.recording {
  background-color: #dc2626;
}

.send-button {
  background-color: #007AFF;
  color: white;
}

.send-button:hover:not(:disabled) {
  background-color: #0056b3;
}

.send-button:disabled, .record-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.pulse {
  transition: transform 0.2s;
}

.pulse:hover {
  transform: scale(1.05);
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.audio-player {
  background-color: #ffffff;
  padding: 12px;
  border-radius: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.audio-player audio {
  width: 100%;
  height: 40px;
  border-radius: 8px;
}

/* Custom scrollbar for messages container */
.messages-container::-webkit-scrollbar {
  width: 8px;
}

.messages-container::-webkit-scrollbar-track {
  background: transparent;
}

.messages-container::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.3);
}

h2 {
  color: #213547;
  margin: 0;
}

.logout-button-position {
  position: absolute;
  top: 1rem;
  right: 20%;  /* Aligns with the right edge of your chat container */
}

/* Add responsive adjustments */
@media (max-height: 600px) {
  .chat-outer-container {
    height: auto;
    height: calc(100vh - 8rem);
  }

  .chat-container {
    height: auto;
    min-height: 250px;
  }
}
</style>

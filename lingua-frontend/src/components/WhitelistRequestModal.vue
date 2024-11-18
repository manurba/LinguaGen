<template>
    <div v-if="show" class="modal-overlay">
        <div class="modal-content">
            <h2>Request Access</h2>
            <p>Your email is not currently whitelisted for access. Would you like to request access?</p>

            <form @submit.prevent="handleSubmit" class="request-form">
                <div class="form-group">
                    <label for="email">Email address:</label>
                    <input
                        type="email"
                        id="email"
                        v-model="email"
                        required
                        :disabled="submitted"
                        placeholder="Enter your email"
                    >
                </div>

                <div class="button-group">
                    <button
                        type="submit"
                        :disabled="submitted"
                        class="submit-btn"
                    >
                        {{ submitted ? 'Request Sent' : 'Request Access' }}
                    </button>
                    <button
                        type="button"
                        @click="$emit('close')"
                        class="cancel-btn"
                    >
                        Close
                    </button>
                </div>
            </form>

            <div v-if="submitted" class="success-message">
                Thank you for your request. We will review it and get back to you soon.
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
    show: Boolean,
    initialEmail: {
        type: String,
        default: ''
    }
});

const emit = defineEmits(['close']);
const email = ref(props.initialEmail);
const submitted = ref(false);

const handleSubmit = async () => {
    try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/request-access`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: email.value }),
        });

        if (!response.ok) {
            throw new Error('Failed to submit request');
        }

        submitted.value = true;
        setTimeout(() => {
            emit('close');
        }, 3000);
    } catch (error) {
        console.error('Error submitting whitelist request:', error);
        alert('Failed to submit request. Please try again later.');
    }
};
</script>

<style scoped>
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.75);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal-content {
    background-color: #1a1a1a;  /* Dark background */
    color: #ffffff;  /* Light text */
    padding: 2rem;
    border-radius: 8px;
    max-width: 500px;
    width: 90%;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.request-form {
    margin-top: 1.5rem;
}

.form-group {
    margin-bottom: 1rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    color: #ffffff;
}

.form-group input {
    width: 100%;
    padding: 0.75rem;
    background-color: #2a2a2a;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    color: #ffffff;
}

.form-group input:focus {
    outline: none;
    border-color: #4285f4;
}

.button-group {
    display: flex;
    gap: 1rem;
    margin-top: 1.5rem;
}

.submit-btn, .cancel-btn {
    padding: 0.75rem 1.5rem;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s ease;
}

.submit-btn {
    background-color: #4285f4;
    color: white;
    border: none;
}

.submit-btn:hover {
    background-color: #3367d6;
}

.submit-btn:disabled {
    background-color: #2a2a2a;
    color: #666;
    cursor: not-allowed;
}

.cancel-btn {
    background-color: transparent;
    border: 1px solid #4a4a4a;
    color: #ffffff;
}

.cancel-btn:hover {
    background-color: #2a2a2a;
}

.success-message {
    margin-top: 1rem;
    padding: 1rem;
    background-color: #1e4620;  /* Darker green background */
    color: #81c995;  /* Light green text */
    border-radius: 4px;
    border: 1px solid #2d5a27;
}

h2 {
    color: #ffffff;
    margin-bottom: 1rem;
}

p {
    color: #cccccc;
    margin-bottom: 1.5rem;
}
</style>

<template>
    <div class="google-login-wrapper">
        <GoogleLogin
            :client-id="yourGoogleClientID"
            :callback="handleCallback"
            :error-callback="handleError"
        >
            <template v-slot="{ signIn }">
                <button @click="signIn" class="google-btn">
                    <img src="/google-icon.svg" alt="Google" class="google-icon" />
                    Sign in with Google
                </button>
            </template>
        </GoogleLogin>

        <WhitelistRequestModal
            :show="showWhitelistModal"
            :initial-email="userEmail"
            @close="showWhitelistModal = false"
        />
    </div>
</template>

<script setup>
import { ref } from 'vue';
import { GoogleLogin } from 'vue3-google-login';
import { useRouter } from 'vue-router';
import { authState } from '../authState';
import WhitelistRequestModal from './WhitelistRequestModal.vue';

const emit = defineEmits(['login-start', 'login-error']);
const router = useRouter();
const yourGoogleClientID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

const showWhitelistModal = ref(false);
const userEmail = ref('');

const handleCallback = async (response) => {
    try {
        emit('login-start');

        if (!response || !response.code) {
            throw new Error('No authorization code received');
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

        const authResponse = await fetch(`${import.meta.env.VITE_API_URL}/auth/google-login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify({ code: response.code }),
            credentials: 'include',
            signal: controller.signal,
            mode: 'cors',
        });

        clearTimeout(timeoutId);

        if (!authResponse.ok) {
            const errorData = await authResponse.json();
            if (authResponse.status === 403) {
                if (response.profile?.email) {
                    userEmail.value = response.profile.email;
                }
                showWhitelistModal.value = true;
                return;
            }
            throw new Error(errorData.detail || 'Authentication failed');
        }


        const authData = await authResponse.json();

        if (!authData.token) {
            throw new Error('No token received from server');
        }

        localStorage.setItem('google_token', authData.token);
        authState.setAuthenticated(true);
        await router.push({ name: 'Chat' });
    } catch (error) {
        if (error.name === 'AbortError') {
            emit('login-error', 'Request timed out. Please try again.');
        } else {
            emit('login-error', error.message || 'Failed to process login. Please try again.');
        }
    }
};

const handleError = (error) => {
    emit('login-error', 'Failed to connect to Google. Please try again.');
};
</script>

<style scoped>
.google-login-wrapper {
    display: flex;
    justify-content: center;
}

.google-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: white;
    color: #333;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
}

.google-btn:hover {
    background-color: #f8f8f8;
}

.google-icon {
    width: 18px;
    height: 18px;
}
</style>

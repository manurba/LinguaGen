// authState.js
import { reactive } from 'vue';
import { isValidToken } from './utils/auth';

const state = reactive({
    isAuthenticated: false,
    setAuthenticated(value) {
        this.isAuthenticated = value;
    }
});

export const authState = {
    ...state,
    checkAuth() {
        return isValidToken();
    }
};

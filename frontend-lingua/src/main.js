import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import VueGoogleLogin from 'vue3-google-signin'
import GoogleLoginButton from './components/GoogleLoginButton.vue';
import router from './router'
import { authState } from './authState';

const app = createApp(App)

const client_id = import.meta.env.VITE_GOOGLE_CLIENT_ID;

// Install the plugin
app.use(VueGoogleLogin, {
  clientId: client_id,
})

const restoreAuthState = () => {
  const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
  // Make sure to integrate this with your global state management or auth service
  authState.isAuthenticated = isAuthenticated;
};

app.component('GoogleLoginButton', GoogleLoginButton);

restoreAuthState();

app.use(router).mount('#app')

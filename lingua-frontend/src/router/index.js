import { createRouter, createWebHistory } from 'vue-router';
import HomePage from '../components/HomePage.vue';
import Login from '../views/Login.vue';
import { isValidToken } from '../utils/auth';
import { authState } from '../authState';

const routes = [
    {
        path: '/c/chat',
        name: 'Chat',
        component: () => import('../components/Chatbot.vue'),
        meta: { requiresAuth: true }
    },
    {
      path: '/',
      component: HomePage,
      name: 'Home'
    },
    {
      path: '/login',
      name: 'Login',
      component: Login,
    },
  ];

const router = createRouter({
  history: createWebHistory(""),
  routes,
});

router.beforeEach((to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!isValidToken()) {
      next({ name: 'Login' });
    } else {
      next();
    }
  } else {
    next();
  }
});

const navigateToPractice = () => {
    if (authState.checkAuth()) {
        router.push({ name: 'Chat' });
    } else {
        router.push({ name: 'Login' });
    }
};

export default router;

import { createRouter, createWebHistory } from 'vue-router';
import HomePage from '../components/HelloWorld.vue';
import { authState } from '../authState';
import Login from '../views/Login.vue';

const routes = [
    {
        path: '/chatbot',
        name: 'Chatbot',
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
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
  if (to.matched.some(record => record.meta.requiresAuth) && !isAuthenticated) {
    next({ name: 'Login' });
  } else {
    next();
  }
});

export default router;

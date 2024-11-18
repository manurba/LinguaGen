import { jwtDecode } from 'jwt-decode';

export const isValidToken = () => {
  const token = localStorage.getItem('google_token');
  if (!token) return false;

  try {
    const decoded = jwtDecode(token);
    return decoded.exp * 1000 > Date.now();  // Convert seconds to milliseconds
  } catch (error) {
    console.error('Token validation error:', error);
    localStorage.removeItem('google_token');  // Clear invalid token
    return false;
  }
};

export const getToken = () => {
  return localStorage.getItem('google_token');
};

export const setToken = (token) => {
  localStorage.setItem('google_token', token);
};

export const removeToken = () => {
  localStorage.removeItem('google_token');
};

export const logout = () => {
  localStorage.removeItem('google_token');
  localStorage.removeItem('isAuthenticated');
};

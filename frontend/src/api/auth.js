import client from './client';

export const login = (username, password) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  return client.post('/login', formData);
};

export const register = (username, email, password) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('email', email);
  formData.append('password', password);
  return client.post('/register', formData);
};
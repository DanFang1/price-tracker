import client from './client';

export const login = (username, password) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  return client.post('/login', formData);
};

export const register = (username, password, email) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  formData.append('email', email);
  return client.post('/register', formData);
};
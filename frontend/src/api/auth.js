import client from './client';

export const login = (username, password) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  return client.post('http://127.0.0.1:5000/login', formData);
};

export const register = (username, password, email) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  formData.append('email', email);
  return client.post('http://127.0.0.1:5000/register', formData);
};
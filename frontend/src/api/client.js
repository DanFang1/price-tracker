import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

const client = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Enable cookies for session
});

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

export const getDashboard = () => {
  return client.get('/dashboard');
};

export const getPriceGraph = (productId) => {
  return client.get(`/price_graph?product_id=${productId}`);
};

export const addProduct = (productUrl, targetPrice) => {
  const formData = new FormData();
  formData.append('product_url', productUrl);
  formData.append('target_price', targetPrice);
  return client.post('/add_product', formData);
};

export const deleteProduct = (productId) => {
  const formData = new FormData();
  formData.append('product_id', productId);
  return client.post('/delete_product', formData);
};

export default client;

import client from './client';

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
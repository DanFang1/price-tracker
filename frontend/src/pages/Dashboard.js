import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDashboard, deleteProduct, addProduct } from '../api/client';
import './Dashboard.css';

export default function Dashboard() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [productUrl, setProductUrl] = useState('');
  const [targetPrice, setTargetPrice] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await getDashboard();
      setProducts(response.data);
    } catch (err) {
      setError('Failed to load dashboard');
      if (err.response?.status === 401) {
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAddProduct = async (e) => {
    e.preventDefault();
    try {
      await addProduct(productUrl, targetPrice);
      setProductUrl('');
      setTargetPrice('');
      setShowAddForm(false);
      fetchProducts();
    } catch (err) {
      alert(err.response?.data || 'Failed to add product');
    }
  };

  const handleDeleteProduct = async (productId) => {
    if (window.confirm('Are you sure?')) {
      try {
        await deleteProduct(productId);
        fetchProducts();
      } catch (err) {
        alert('Failed to delete product');
      }
    }
  };

  if (loading) return <div className="dashboard">Loading...</div>;

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Price Tracker</h1>
        <button onClick={() => navigate('/login')}>Logout</button>
      </header>

      {error && <p className="error">{error}</p>}

      <button 
        className="add-btn"
        onClick={() => setShowAddForm(!showAddForm)}
      >
        {showAddForm ? 'Cancel' : '+ Add Product'}
      </button>

      {showAddForm && (
        <form className="add-product-form" onSubmit={handleAddProduct}>
          <input
            type="url"
            placeholder="Product URL"
            value={productUrl}
            onChange={(e) => setProductUrl(e.target.value)}
            required
          />
          <input
            type="number"
            placeholder="Target Price"
            step="0.01"
            value={targetPrice}
            onChange={(e) => setTargetPrice(e.target.value)}
            required
          />
          <button type="submit">Add Product</button>
        </form>
      )}

      <div className="products-grid">
        {products.map((product) => (
          <div key={product[0]} className="product-card">
            <h3>{product[1]}</h3>
            <p>Current Price: <strong>${product[2]}</strong></p>
            <p>Target Price: <strong>${product[3]}</strong></p>
            <button
              className="delete-btn"
              onClick={() => handleDeleteProduct(product[0])}
            >
              Delete
            </button>
          </div>
        ))}
      </div>

      {products.length === 0 && (
        <p className="empty-state">No products tracked yet. Add one to get started!</p>
      )}
    </div>
  );
}

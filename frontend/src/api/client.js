import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

const client = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Enable cookies for session
});

export default client;

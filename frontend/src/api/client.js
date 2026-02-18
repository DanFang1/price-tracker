import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true, // Enable cookies for session
});

export default client;

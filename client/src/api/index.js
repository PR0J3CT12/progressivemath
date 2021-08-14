import axios from 'axios';

const API = axios.create({ baseURL: 'http://127.0.0.1:5000' });

export const signIn = (formData) => API.post('/auth', formData);
export const getStudent = (studentId) => API.get(`/student/${studentId}`);
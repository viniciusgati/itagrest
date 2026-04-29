import axios from 'axios';

// A URL da API será lida da variável de ambiente NEXT_PUBLIC_API_URL.
// Isso permite configurar a URL dinamicamente para desenvolvimento, Docker e produção.
const envBaseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Remove barra final para evitar barras duplas na concatenação (//api/v1)
const baseURL = envBaseURL.replace(/\/$/, '');

const api = axios.create({
  baseURL: `${baseURL}/api/v1`,
  withCredentials: true, // Importante para enviar cookies de autenticação se houver
});

// Interceptor para injetar o token em todas as requisições
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para tratar erros globais (Ex: Sessão expirada)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Se o backend disser que o token é inválido/expirou
      localStorage.removeItem('token');
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Função helper para construir a URL de imagens
export const getImageUrl = (path: string | null | undefined) => {
  if (!path) return '/placeholder.png'; // Retorna um placeholder se não houver imagem
  return `${baseURL}${path}`;
};


export default api;

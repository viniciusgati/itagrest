import axios from 'axios';

// A URL da API será lida da variável de ambiente NEXT_PUBLIC_API_URL.
// Isso permite configurar a URL dinamicamente para desenvolvimento, Docker e produção.
const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${baseURL}/api/v1`,
  withCredentials: true, // Importante para enviar cookies de autenticação se houver
});

// Função helper para construir a URL de imagens
export const getImageUrl = (path: string | null | undefined) => {
  if (!path) return '/placeholder.png'; // Retorna um placeholder se não houver imagem
  return `${baseURL}${path}`;
};


export default api;

# Stage 1: Build a aplicação Next.js
FROM node:20-alpine AS builder

WORKDIR /app

# Adiciona argumentos de build para variáveis públicas do Next.js
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Copia package.json e package-lock.json
COPY package*.json ./

# Instala dependências
RUN npm install

# Copia o resto do código da aplicação
COPY . .

# Constrói a aplicação para produção
RUN npm run build

# Stage 2: Cria a imagem final otimizada
FROM node:20-alpine

WORKDIR /app

# Copia os artefatos de build da stage anterior
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public

# Expor a porta que o Next.js usa
EXPOSE 3000

# Comando para iniciar o servidor Next.js em produção usando a porta do Railway
CMD ["sh", "-c", "npm start -- -p ${PORT:-3000}"]

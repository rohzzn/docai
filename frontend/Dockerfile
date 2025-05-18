# Stage 1: Build React App
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json ./
COPY package-lock.json ./
RUN npm install
COPY . ./

CMD ["npm", "start"]
# Build stage
FROM node:20 AS build-stage

WORKDIR /app

ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build

# Production stage
FROM nginx:stable-alpine as production-stage

# Copy built assets from build stage to nginx serve directory
COPY --from=build-stage /app/dist /usr/share/nginx/html

COPY nginx/custom_nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

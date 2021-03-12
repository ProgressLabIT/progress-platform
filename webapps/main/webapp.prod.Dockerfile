FROM node:15 AS builder

WORKDIR /app

COPY package.json .
COPY package-lock.json .

RUN npm install

COPY .eslintrc.js .
COPY babel.config.js .
COPY vue.config.js .
COPY src ./src
COPY public ./public

FROM builder AS built
RUN npm run build

FROM nginx:1.18
COPY nginx.prod.conf /etc/nginx/nginx.conf
COPY --from=built /app/dist /usr/share/nginx/html

FROM node:16 AS builder
WORKDIR /app
COPY package.json .
COPY yarn.lock .
RUN yarn

FROM builder AS built
COPY public ./public
COPY jsonfig.json postcss.config.js quasar.config.json
COPY src ./src
RUN yarn quasar build

FROM nginx:1.18
COPY nginx.prod.conf /etc/nginx/nginx.conf
COPY --from=built /app/dist /usr/share/nginx/html

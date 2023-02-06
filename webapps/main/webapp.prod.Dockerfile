FROM node:lts-alpine as global-deps-stage
RUN npm i --location=global @quasar/cli@latest

FROM global-deps-stage as develop-stage
WORKDIR /app
COPY package.json .
COPY yarn.lock .
RUN yarn

FROM develop-stage AS build-stage
COPY . .
RUN yarn quasar build -m spa

FROM nginx:1.18
COPY nginx.prod.conf /etc/nginx/nginx.conf
COPY --from=build-stage /app/dist/spa /usr/share/nginx/html


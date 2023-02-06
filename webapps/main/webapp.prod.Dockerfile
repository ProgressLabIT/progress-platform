FROM node:lts-alpine as global-deps-stage
RUN npm i --location=global @quasar/cli@latest

FROM global-deps-stage as develop-stage
WORKDIR /app
COPY package.json .
COPY yarn.lock .
RUN yarn

FROM develop-stage AS config-stage
COPY .quasar ./.quasar
COPY public ./public
COPY jsconfig.json postcss.config.js index.html .
COPY .eslintrc.js .eslintignore .
COPY quasar.config.js .

FROM config-stage AS build-stage
COPY src ./src
RUN yarn quasar build -m spa

FROM nginx:1.18
COPY nginx.prod.conf /etc/nginx/nginx.conf
COPY --from=build-stage /app/dist/spa /usr/share/nginx/html


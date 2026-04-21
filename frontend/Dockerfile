FROM node:14-alpine

WORKDIR /app/

COPY . /app

RUN npm install

RUN npm run build

RUN npm install -g serve

EXPOSE 3001

ENTRYPOINT ["serve", "-s", "build"]
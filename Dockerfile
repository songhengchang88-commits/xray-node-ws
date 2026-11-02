FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install --production

FROM node:20-alpine
WORKDIR /app
RUN apk add --no-cache ca-certificates tzdata
COPY --from=builder /app/node_modules ./node_modules
COPY . .
RUN node scripts/install-xray.js

ENV PORT=3000 \
    XRAY_PORT=10000 \
    WSPATH=/ws

EXPOSE 3000

CMD ["node", "server.js"]

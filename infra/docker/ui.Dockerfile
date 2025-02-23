FROM node:20-alpine AS builder
WORKDIR /app
COPY ui/package*.json ./

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=NEXT_PUBLIC

# dep needs to be forced kinda bad maybe ill fix (probably not)
RUN npm install --force
COPY ui/ .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV production
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["npm", "start"]

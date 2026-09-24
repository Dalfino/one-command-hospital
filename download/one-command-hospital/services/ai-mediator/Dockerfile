FROM node:20-alpine
WORKDIR /app
# audit.js + metrics.js are part of the runtime contract — ALL runtime files
# must be copied (v0.2 shipped only main.js and crashed on missing import).
COPY package.json ./
RUN npm install --omit=dev
COPY main.js medplum-auth.js audit.js metrics.js ./
# Non-root runtime + writable audit dir (named volume inherits ownership).
RUN mkdir -p /app/audit && chown -R node:node /app/audit
USER node
EXPOSE 3000
CMD ["node", "main.js"]

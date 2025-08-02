FROM node:20-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y git python3 make g++ && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package*.json .npmrc ./

RUN rm -f package-lock.json && \
    npm cache clean --force && \
    npm install --force --legacy-peer-deps --no-audit --no-fund && \
    npm rebuild

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
#!/bin/bash

echo "🧹 Cleaning up node_modules and package-lock.json..."
rm -rf node_modules package-lock.json

echo "📦 Installing dependencies with legacy peer deps..."
npm install --legacy-peer-deps

echo "✅ Dependencies reset successfully!" 
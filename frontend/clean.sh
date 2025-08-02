#!/bin/bash

echo "🧹 Cleaning up all dependency files..."
rm -rf node_modules package-lock.json

echo "📦 Installing fresh dependencies..."
npm install --legacy-peer-deps

echo "✅ Clean installation completed!" 
#!/bin/bash

# Exit immediately on error
set -e

echo "📦 Installing base dependencies..."
npm install

echo "🎨 Installing Tailwind CSS and related packages..."
npm install -D tailwindcss postcss autoprefixer

echo "💫 Installing animations and routing..."
npm install framer-motion react-router-dom

# Only initialize Tailwind config if not present
if [ ! -f tailwind.config.js ]; then
  echo "🛠️ Initializing Tailwind config..."
  npx tailwindcss init -p
fi

# Ensure shadcn components are scaffolded
if [ ! -f components.json ]; then
  echo "🧱 Setting up shadcn components..."
  npx shadcn@latest init
fi

echo "🧩 Adding common UI components (label, textarea)..."
npx shadcn@latest add label textarea

echo "✅ Tailwind & shadcn-ui configured."
echo "🚀 You're ready! Run the dev server with:"
echo "   npm run dev"

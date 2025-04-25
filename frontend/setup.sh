#!/bin/bash
echo "📦 Installing dependencies..."
npm install

npm install tailwindcss postcss autoprefixer framer-motion
npx tailwindcss init -p

echo "✅ Tailwind & Vite configured."
echo "💻 Run your app with: npm run dev"


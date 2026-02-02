#!/bin/bash
# Little Red Shrimp 🍤 - Quick Push Script
# Created by Kestrel 🦅

REPO_URL="https://github.com/frankie-yanxu/xiaohongxia.git"

echo "🍤 Initializing Little Red Shrimp..."
git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"

echo "🦅 Spreading wings (Pushing to GitHub)..."
git branch -M main
git push -u origin main

echo "✨ Done! Your sanctuary is now on GitHub."

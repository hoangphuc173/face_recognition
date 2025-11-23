# Configuration Guide

This directory contains configuration templates for the Face Recognition System.

## 📂 Structure

- **`env_templates/`**: Contains example `.env` files.
  - **`root.env.example`**: The master configuration template. Use this for local development.
  - **`aws.env.example`**: Specific configuration for AWS deployment (if needed separately).

## 🚀 How to Use

1. **Local Development**:
   Copy `env_templates/root.env.example` to the root directory as `.env`:
   ```bash
   cp config/env_templates/root.env.example .env
   ```
   Then edit `.env` with your actual credentials.

2. **Frontend**:
   The frontend (`face-recognition-app`) has its own `.env` file located at `face-recognition-app/.env`.

## ⚠️ Security

- **NEVER** commit `.env` files to version control.
- `.env` is already added to `.gitignore`.

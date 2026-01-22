#!/usr/bin/env bash
# Render build script for Sales Automation Backend

# Exit on error
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

"""Entrypoint for seeding the database: python seed.py"""
import sys
import os

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.seed import seed_database

if __name__ == "__main__":
    seed_database()

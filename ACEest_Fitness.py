"""
ACEest Fitness & Gym Management System - Production Application Entrypoint
Course: CSIZG514 / SEZG514 - Introduction to DevOps (Assignment 2)
Author: Kiran K Das (Student ID: 2025TM93130)
Repository: https://github.com/KiranKDas/aceest_gym_app
"""

import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)

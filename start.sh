#!/bin/bash
python3 -m keep_alive &  # Start Flask server in the background
python3 main.py          # Start the bot

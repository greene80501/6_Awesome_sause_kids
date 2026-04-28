#!/usr/bin/env python3
# main.py — Entry point for Tavern Looter
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.game import Game


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()

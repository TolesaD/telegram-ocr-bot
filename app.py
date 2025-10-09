from bot import ExpenseTrackerBot
from config import Config
from telegram.ext import Application

def main():
    bot = ExpenseTrackerBot()
    bot.run()

if __name__ == '__main__':
    main()
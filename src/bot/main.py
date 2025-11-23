import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import handlers
from ..db.base import get_db
from ..services.rng_service import RNGService
from ..services.payout_service import PayoutService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class LotteryBot:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.db_url = os.getenv('DATABASE_URL', 'sqlite:///./lottery.db')
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Initialize services
        self.rng_service = RNGService(os.getenv('SEED_ENCRYPTION_KEY', 'default-key-change-in-production'))
        self.payout_service = PayoutService(self.SessionLocal())
        
        # Create application
        self.application = Application.builder().token(self.bot_token).build()
        
        self._setup_handlers()

    def _setup_handlers(self):
        # Command handlers
        self.application.add_handler(CommandHandler("start", handlers.start))
        self.application.add_handler(CommandHandler("balance", handlers.balance))
        self.application.add_handler(CommandHandler("setclientseed", handlers.set_client_seed))
        self.application.add_handler(CommandHandler("verify", handlers.verify_round))
        self.application.add_handler(CommandHandler("commit", handlers.get_commitment))
        self.application.add_handler(CommandHandler("reveal", handlers.reveal_seed))
        self.application.add_handler(CommandHandler("forced_history", handlers.forced_history))
        
        # Betting handlers
        self.application.add_handler(MessageHandler(filters.Regex(r'^/N(\d+)$'), handlers.place_bet))
        self.application.add_handler(MessageHandler(filters.Regex(r'^/L(\d+)$'), handlers.place_bet))
        self.application.add_handler(MessageHandler(filters.Regex(r'^/C(\d+)$'), handlers.place_bet))
        self.application.add_handler(MessageHandler(filters.Regex(r'^/Le(\d+)$'), handlers.place_bet))
        self.application.add_handler(MessageHandler(filters.Regex(r'^/S(\d{6})\s+(\d+)$'), handlers.place_specific_bet))

    def run(self, mode='polling'):
        if mode == 'webhook':
            # Webhook configuration for production
            webhook_url = os.getenv('WEBHOOK_URL')
            port = int(os.getenv('PORT', 8000))
            
            self.application.run_webhook(
                listen="0.0.0.0",
                port=port,
                url_path=self.bot_token,
                webhook_url=f"{webhook_url}/{self.bot_token}"
            )
        else:
            # Polling for development
            self.application.run_polling()

def main():
    bot = LotteryBot()
    
    # Check if we should use webhook mode
    use_webhook = os.getenv('USE_WEBHOOK', 'false').lower() == 'true'
    
    bot.run(mode='webhook' if use_webhook else 'polling')

if __name__ == '__main__':
    main()

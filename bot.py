#!/usr/bin/env python3
"""
Telegram Image-to-Text Converter Bot
Railway Comprehensive Debug Version
"""
import os
import logging
import sys
import asyncio

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def comprehensive_debug():
    """Comprehensive environment debugging"""
    logger.info("🔍 COMPREHENSIVE DEBUG STARTED")
    
    # 1. Check if we're on Railway
    is_railway = 'RAILWAY_ENVIRONMENT' in os.environ
    logger.info(f"🚄 Running on Railway: {is_railway}")
    
    # 2. List ALL environment variables
    all_vars = dict(os.environ)
    logger.info(f"📋 Total environment variables: {len(all_vars)}")
    
    # 3. Show all variable names (without values for security)
    logger.info("📝 All environment variable NAMES:")
    for key in sorted(all_vars.keys()):
        logger.info(f"   - {key}")
    
    # 4. Check for BOT_TOKEN specifically
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    logger.info(f"🔑 BOT_TOKEN exists: {BOT_TOKEN is not None}")
    
    if BOT_TOKEN:
        logger.info(f"✅ BOT_TOKEN length: {len(BOT_TOKEN)}")
        logger.info(f"✅ BOT_TOKEN starts with: {BOT_TOKEN[:10]}...")
        logger.info(f"✅ BOT_TOKEN ends with: ...{BOT_TOKEN[-10:]}")
        
        # Check token format
        if ':' in BOT_TOKEN:
            logger.info("✅ BOT_TOKEN format appears correct (contains colon)")
        else:
            logger.warning("⚠️ BOT_TOKEN format may be incorrect (no colon)")
    else:
        logger.error("❌ BOT_TOKEN is None/not set")
    
    # 5. Check for common alternative names
    alternative_names = [
        'TELEGRAM_BOT_TOKEN', 'BOTTOKEN', 'TELEGRAM_TOKEN', 
        'BOT_TOKEN', 'TOKEN', 'TELEGRAM_BOT_TOKEN'
    ]
    
    logger.info("🔄 Checking alternative variable names:")
    for name in alternative_names:
        value = os.getenv(name)
        if value:
            logger.info(f"   ✅ FOUND: {name} = {value[:5]}... (length: {len(value)})")
        else:
            logger.info(f"   ❌ NOT FOUND: {name}")
    
    # 6. Check file system
    logger.info("📁 File system check:")
    try:
        current_dir = os.getcwd()
        logger.info(f"   Current directory: {current_dir}")
        
        files = os.listdir('.')
        logger.info(f"   Files in current directory: {len(files)} items")
        for file in sorted(files)[:10]:  # Show first 10 files
            logger.info(f"     - {file}")
            
        if '.env' in files:
            logger.info("   📄 .env file exists locally")
            try:
                with open('.env', 'r') as f:
                    env_content = f.read()
                    if 'BOT_TOKEN' in env_content:
                        logger.info("   ✅ BOT_TOKEN found in .env file")
                    else:
                        logger.info("   ❌ BOT_TOKEN not in .env file")
            except Exception as e:
                logger.error(f"   ❌ Error reading .env: {e}")
        else:
            logger.info("   📄 No .env file found")
            
    except Exception as e:
        logger.error(f"   ❌ File system error: {e}")
    
    # 7. Python environment
    logger.info("🐍 Python environment:")
    logger.info(f"   Python version: {sys.version}")
    logger.info(f"   Python path: {sys.executable}")
    logger.info(f"   Working directory: {os.getcwd()}")
    
    return BOT_TOKEN

def test_telegram_connection(token):
    """Test if we can connect to Telegram with the token"""
    logger.info("🔗 Testing Telegram connection...")
    try:
        import telegram
        from telegram import Bot
        
        bot = Bot(token=token)
        
        # Test synchronous connection (simpler)
        try:
            me = bot.get_me()
            logger.info(f"✅ Telegram connection SUCCESSFUL!")
            logger.info(f"✅ Bot: @{me.username} ({me.first_name})")
            logger.info(f"✅ Bot ID: {me.id}")
            return True
        except Exception as e:
            logger.error(f"❌ Telegram connection failed: {e}")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Telegram library import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error testing Telegram: {e}")
        return False

async def async_test_telegram_connection(token):
    """Test Telegram connection asynchronously"""
    logger.info("🔗 Testing Telegram connection (async)...")
    try:
        from telegram import Bot
        
        bot = Bot(token=token)
        me = await bot.get_me()
        logger.info(f"✅ Async Telegram connection SUCCESSFUL!")
        logger.info(f"✅ Bot: @{me.username} ({me.first_name})")
        return True
    except Exception as e:
        logger.error(f"❌ Async Telegram connection failed: {e}")
        return False

def main():
    """Main debug function"""
    logger.info("🤖 STARTING COMPREHENSIVE DEBUG")
    logger.info("=" * 60)
    
    try:
        # Comprehensive debug
        bot_token = comprehensive_debug()
        
        logger.info("=" * 60)
        
        if not bot_token:
            logger.error("❌ CRITICAL: BOT_TOKEN not available")
            logger.error("💡 SOLUTION: Please check:")
            logger.error("   1. Go to Railway → Your Project → Variables")
            logger.error("   2. Ensure BOT_TOKEN is set (exactly this name)")
            logger.error("   3. Ensure the value is your Telegram bot token")
            logger.error("   4. Redeploy after making changes")
            return 1
        
        # Test Telegram connection
        logger.info("🔄 Testing Telegram connection...")
        sync_success = test_telegram_connection(bot_token)
        
        if not sync_success:
            logger.error("❌ Telegram connection test failed")
            logger.error("💡 Possible issues:")
            logger.error("   - Bot token is invalid/expired")
            logger.error("   - Network connectivity issues")
            logger.error("   - Bot was deleted from @BotFather")
            return 1
        
        # Test async connection
        logger.info("🔄 Testing async Telegram connection...")
        try:
            async_success = asyncio.run(async_test_telegram_connection(bot_token))
            if not async_success:
                logger.error("❌ Async Telegram connection test failed")
                return 1
        except Exception as e:
            logger.error(f"❌ Async test error: {e}")
            return 1
        
        logger.info("=" * 60)
        logger.info("✅ ALL TESTS PASSED! Bot should work correctly.")
        logger.info("💡 Next steps:")
        logger.info("   - Deploy the final bot version")
        logger.info("   - Monitor Railway logs")
        logger.info("   - Test by sending /start to your bot")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Comprehensive debug failed: {e}")
        return 1

if __name__ == '__main__':
    result = main()
    sys.exit(result)
"""
Main entry point for WhatsApp Form Auto-Fill System.

This is the MVP version (Phase 1) that processes form URLs directly.
Phase 2 will add WhatsApp integration.
"""
import sys
from loguru import logger

from config import settings
from orchestrator import FormFillingOrchestrator


def setup_logging():
    """Configure loguru logging."""
    # Remove default handler
    logger.remove()
    
    # Add console handler with colors
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )
    
    # Add file handler if enabled
    if settings.log_to_file:
        log_file = f"{settings.logs_dir}/whatsapp_form_filler.log"
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            level=settings.log_level,
            rotation="1 day",
            retention=f"{settings.log_retention_days} days",
            compression="zip",
        )
    
    logger.info("Logging configured")


def main():
    """Main entry point."""
    setup_logging()
    
    logger.info("=" * 70)
    logger.info("🤖 WhatsApp Form Auto-Fill System - MVP Phase 1")
    logger.info("=" * 70)
    logger.info(f"👤 Student: {settings.student_name}")
    logger.info(f"🆔 ID: {settings.student_id}")
    logger.info(f"📁 Database: {settings.database_path}")
    logger.info(f"📂 Logs: {settings.logs_dir}")
    logger.info("=" * 70)
    
    # Check if OpenAI is configured
    if not settings.has_openai and settings.use_ai_fallback:
        logger.warning("⚠️  OpenAI API key not configured - AI fallback disabled")
    
    # Initialize orchestrator
    with FormFillingOrchestrator() as orchestrator:
        # Check if URL provided as argument
        if len(sys.argv) > 1:
            # URL provided as command-line argument
            form_url = sys.argv[1]
            logger.info(f"\n📋 Processing URL from command line: {form_url}\n")
            
            success = orchestrator.process_form(form_url)
            
            if success:
                logger.success("\n✅ Form processing complete!\n")
            else:
                logger.error("\n❌ Form processing failed!\n")
            
            # Show stats
            stats = orchestrator.get_stats()
            logger.info(f"📊 Today's Stats: {stats['daily']}")
            logger.info(f"⏱️  Rate Limiter: {stats['rate_limiter']}\n")
        else:
            # Interactive mode (fallback)
            logger.info("\n" + "=" * 70)
            logger.info("🧪 INTERACTIVE MODE")
            logger.info("=" * 70)
            logger.info("\nUsage:")
            logger.info("  python main.py <form_url>")
            logger.info("\nOr paste URL below (type 'quit' to exit):\n")
            
            while True:
                try:
                    form_url = input("Form URL: ").strip()
                    
                    if form_url.lower() in ['quit', 'exit', 'q']:
                        logger.info("👋 Exiting...")
                        break
                    
                    if not form_url:
                        continue
                    
                    if 'forms.office.com' not in form_url:
                        logger.warning("⚠️  Only Microsoft Forms is supported in MVP")
                        continue
                    
                    # Process the form
                    success = orchestrator.process_form(form_url)
                    
                    if success:
                        logger.success("\n✅ Form processing complete!\n")
                    else:
                        logger.error("\n❌ Form processing failed!\n")
                    
                    # Show stats
                    stats = orchestrator.get_stats()
                    logger.info(f"📊 Today's Stats: {stats['daily']}")
                    logger.info(f"⏱️  Rate Limiter: {stats['rate_limiter']}\n")
                    
                    logger.info("Ready for next form (or 'quit' to exit):\n")
                
                except KeyboardInterrupt:
                    logger.info("\n\n👋 Interrupted by user, exiting...")
                    break
                except Exception as e:
                    logger.exception(f"Unexpected error: {e}")
    
    logger.info("\n" + "=" * 70)
    logger.info("🛑 System shutdown complete")
    logger.info("=" * 70)


if __name__ == "__main__":
    try:
        # Run main function
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)

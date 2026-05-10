from core.config import get_settings
from core.logging import configure_logging

from app.bot.client import ModularBot


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    ModularBot().run(settings.discord_bot_token, log_handler=None)


if __name__ == "__main__":
    main()

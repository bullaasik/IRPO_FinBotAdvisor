from stoa_sdk.StoaSDK.settings import get_env_var, run_settings_validation
from telegram_app import TelegramApp

class App:
    tg: TelegramApp

    def __init__(self):
        self._init_services()
        self._init_tg()

    def _init_services(self):
        # services.add_service(TelegramBotCacheService, 'tg_cach')
        pass

    def _init_tg(self):
        self.tg = TelegramApp(get_env_var('TG_BOT_TOKEN'))
        run_settings_validation()

    def start(self):
        self.tg.start()


def make_app():
    app = App()
    return app


app = make_app()

if __name__ == '__main__':
    app.start()

from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters, CommandHandler

from chatbot import ChatBot


class TelegramApp:
    _token: str
    tg: Application
    chatbot: ChatBot


    def __init__(self, token: str):
        self._token = token
        self._build_chatbot()
        self._build_app()

    
    def _build_chatbot(self):
        self.chatbot = ChatBot()

    
    def _build_app(self):
        _token = self._token
        self.tg = tg = Application.builder().token(_token).build()
        
        # common message handler
        tg.add_handler(CommandHandler(command='ns', callback=self._new_session))
        tg.add_handler(CommandHandler(command='ls', callback=self._list_sessions))
        tg.add_handler(MessageHandler(filters=filters.ALL, callback=self._proxy_message))
    
    def start(self):
        self.tg.run_polling(allowed_updates=Update.ALL_TYPES)

    
    async def _new_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        session_name = context.args[0] if len(context.args) > 0 else None
        user = update.message.from_user
        user_id = user.id

        new_session_name = self.chatbot.add_session(user_id, session_name)
        await update.message.reply_text(f'New session added: {new_session_name}')
        # add and activate_session



    async def _list_sessions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.message.from_user
        user_id = user.id
        active_session = self.chatbot.get_active_session(user_id)
        def _format_session_name(s):
            prefix = "*" if s == active_session else ""
            return f'{prefix}{s}{prefix}'
        sessions_text = '\n'.join(
            map(
                _format_session_name,
                self.chatbot.list_sessions(user_id)
            )
        )
        await update.message.reply_text(sessions_text)

    
    async def _proxy_message(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.message.from_user
        user_id = user.id
        response = self.chatbot.send_message(user_id, update.message.text)
        await update.message.reply_text(response)

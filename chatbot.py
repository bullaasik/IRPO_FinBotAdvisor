import time
import yaml
import openai
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from pairs import get_all_currencies


UserIdType = str | int


SYSTEM_ROLE = 'system'
USER_ROLE = 'user'
CHAT_ROLE = 'assistant'


@dataclass
class MessageMeta:
    role: str = field(default=USER_ROLE)
    content: str = field(default='')


@dataclass
class SessonMeta:
    conversation: list = field(default_factory=list)

    def add_message(self, role, message):
        self.conversation.append(MessageMeta(role, message))

    def update_message(self, message_id, message):
        self.conversation[message_id] = message

    def __post_init__(self):
        pass

    def dump_conversation(self):
        return list(map(asdict, self.conversation))


@dataclass
class SessionMetaWithPreprompt(SessonMeta):
    INITIAL_PREPROMPT: str = ''

    def __post_init__(self):
        # calling SessionMeta __post_init__
        super().__post_init__()
        
        # adding preprompt message
        # should be the first message in conversation
        self.conversation.insert(0, MessageMeta(SYSTEM_ROLE, self.INITIAL_PREPROMPT))

    
    def update_preprompt(self, message):
        self.update_message(0, MessageMeta(SYSTEM_ROLE, message))



_active_session_default_factory = lambda: str(int(time.time()))


class OpenAIChat:

    def complete(self, messages: list):
        complete = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return complete['choices'][0]['message']['content']


@dataclass
class UserMeta:
    active_session_name: str = field(default_factory=_active_session_default_factory)
    sessions: dict = field(default_factory=lambda: defaultdict(SessionMetaWithPreprompt))

    def __post_init__(self):
        if self.active_session_name not in self.sessions:
            self.sessions[self.active_session_name] = SessionMetaWithPreprompt()
    
    def add_session(self, session_id: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionMetaWithPreprompt()
    
    def set_active_session(self, session_id: str):
        if session_id not in self.sessions:
            raise ValueError(f"Session with session_id={session_id} not found")
        self.active_session_name = session_id

    def list_sessions(self):
        return list(self.sessions.keys())
    
    @property
    def active_session(self):
        return self.sessions[self.active_session_name]


cache = defaultdict(UserMeta)

def truncate_text(text, max_length):
    return text[:max_length]


class ChatBot:
    
    _chatbot: OpenAIChat

    def __init__(self):

        self._chatbot = OpenAIChat()

    def add_session(self, user_id: UserIdType, session_name: str | None):
        """
        # Add session for user
        
        Adding session for user with user_id and session_name and activate it as active_session
        If session_name is undefined, creating session with name like timestamp
        If session_name is defined, creating session with name like session_name
        """
        user_cache = cache[user_id]
        if session_name is None:
            session_name = _active_session_default_factory()
        user_cache.add_session(session_name)
        user_cache.set_active_session(session_name)
        return session_name
    
    def get_active_session(self, user_id: UserIdType):
        """
        # Get active session for user
        
        Return active session for user with user_id
        """
        user_cache = cache[user_id]
        return user_cache.active_session_name


    def list_sessions(self, user_id: UserIdType):
        """
        # List sessions for user
        
        List sessions for user with user_id
        """
        user_cache = cache[user_id]
        return user_cache.list_sessions()
    

    def send_message(self, user_id: UserIdType, message: str):
        user_cache = cache[user_id]
        active_session = user_cache.active_session

        # Обрезаем текст сообщения до максимальной длины
        message_to_model = truncate_text(message, 4096)

        # Обновляем препромпт и добавляем сообщение пользователя
        active_session.update_preprompt(self._get_preprompt(user_id))
        active_session.add_message(USER_ROLE, message_to_model)

        # Отправляем сообщение в модель и получаем ответ
        response = self._chatbot.complete(active_session.dump_conversation())

        # Добавляем ответ модели к истории разговора
        active_session.add_message(CHAT_ROLE, response)

        return response
    
    def _get_preprompt(self, user_id):
        # Получаем информацию о валютных парах
        api_key = "f4432020496043c8bdc9dc35cfe496a0"
        currencies_info = get_all_currencies(api_key)

        # Подготавливаем информацию о валютных парах
        currency_pairs_info = "\n".join(f"{currency}: {rate}" for currency, rate in list(currencies_info.items())[:5])

        return currency_pairs_info
    
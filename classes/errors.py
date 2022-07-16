class UserNotFoundError(BaseException):
    def __init__(self, chat_id):
        super(f'Не был найден пользователь с chat_id = {chat_id} в базе данных')

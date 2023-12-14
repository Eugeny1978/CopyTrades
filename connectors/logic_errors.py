class LogicErrors(Exception):

    def __init__(self, *args):
        self.message = args[0] if args else None

    def __str__(self):
        if self.message:
            return '| LogicError, {0} |'.format(self.message)
        else:
            return '| Ошибка класса LogicError |'
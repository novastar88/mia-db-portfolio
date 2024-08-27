
class ObjectEmpty(Exception):
    pass


class ObjectIsNone(Exception):
    pass


class ObjectWrongType(Exception):
    pass


class UnexpectedExit(Exception):
    def __init__(self) -> None:
        super().__init__(self, "unexpected function exit")


if __name__ == "__main__":
    pass

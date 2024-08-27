from loguru import logger
import general._logging


class Action:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        raise NotImplementedError

    def _preparation(self):
        pass

    def _do(self):
        raise NotImplementedError

    def _effects(self):
        pass

    def execute(self):
        logger.debug(
            f"start executing action {str(self)}, start executing _preparation")
        self._preparation()
        logger.debug(f"{str(self)} end of _preparation, start executing _do")
        self._do()
        logger.debug(
            f"{str(self)} end of _do execution, start executing _effects")
        self._effects()
        logger.debug(f"{str(self)} end of _effects execution, end of action")

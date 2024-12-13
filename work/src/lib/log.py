from logging import getLogger, DEBUG, INFO, WARNING, ERROR, StreamHandler, Formatter

LOG = getLogger("inventory")

# ログの出力先の設定
handler = StreamHandler()  # 標準出力
LOG.addHandler(handler)

# ログフォーマットの設定
formatter = Formatter("%(asctime)s: %(module)s.%(funcName)s:%(lineno)d [%(levelname)s]: %(message)s")
handler.setFormatter(formatter)

def set_level(
        level: str
        ) -> bool:
    """
    ログレベルを設定します。

    Args:
        level (str): コマンドライン引数で指定したログレベル
    """

    match level:
        case "debug":
            LOG.setLevel(DEBUG)
            return True
        case "info":
            LOG.setLevel(INFO)
            return True
        case "warning":
            LOG.setLevel(WARNING)
            return True
        case "error":
            LOG.setLevel(ERROR)
            return True
        case _:
            print(f"[ERROR]: Log level({level}) is unexpected.")
            return False
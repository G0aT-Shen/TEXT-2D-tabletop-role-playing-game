"""绝夜之旅 — Journey of the Final Night — 入口."""

import sys
import os
import traceback

import pygame

from game.engine import Game


def main():
    try:
        game = Game()
        game.run()
    except Exception:
        # 无控制台模式用消息框显示错误
        err = traceback.format_exc()
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, err, "绝夜之旅 - 错误", 0x10)
        except Exception:
            pass
        # 写入日志到项目目录
        try:
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error.log")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(err)
        except Exception:
            pass
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()

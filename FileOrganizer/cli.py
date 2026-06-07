"""
文件自动归档 - 命令行模式（保留原有 MVP 使用方式）
"""

from organizer import OrganizerService


def main():
    print("文件自动归档助手（命令行模式）")
    print("-" * 30)

    service = OrganizerService()
    service.start()

    print()
    print("正在监控 input 文件夹...（按 Ctrl+C 停止）")

    try:
        if service._thread:
            service._thread.join()
    except KeyboardInterrupt:
        print()
        print("已停止监控。")
        service.stop()


if __name__ == "__main__":
    main()

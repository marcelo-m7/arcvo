import asyncio

from app.dashboard.launcher import run_dashboard


def main() -> None:
    asyncio.run(run_dashboard())


if __name__ == "__main__":
    main()

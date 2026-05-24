import asyncio

from app.hermes.launcher import run_hermes


def main() -> None:
    asyncio.run(run_hermes())


if __name__ == "__main__":
    main()

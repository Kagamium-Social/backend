from kagamium.bootstrap import ensure_runtime_dependencies


def run() -> None:
    ensure_runtime_dependencies()

    from kagamium.main import main

    main()


if __name__ == "__main__":
    run()

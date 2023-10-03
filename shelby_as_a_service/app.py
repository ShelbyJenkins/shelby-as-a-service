import argparse

from app_base import AppBase


def main():
    """
    By default, this script runs the web app locally.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "app_name",
        type=str,
        nargs="?",
        help=f"Runs with a configuration from apps/<app_name>/app_config.json.",
    )
    args = parser.parse_args()

    if args.app_name:
        app_name = args.app_name
    else:
        app_name = "base"

    print(f"app.py is being run as: {app_name}")
    app = AppBase.get_app(app_name)
    app.setup_app()
    app.run_sprites()


if __name__ == "__main__":
    main()

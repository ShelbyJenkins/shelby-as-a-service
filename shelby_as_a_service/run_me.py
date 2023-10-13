import argparse

from app_config.app_base import AppBase


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
    AppBase.setup_app(app_name)
    AppBase.run_sprites()


if __name__ == "__main__":
    main()

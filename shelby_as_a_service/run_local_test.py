import argparse
import sys

from app.app_base import AppBase
from extensions.content_aggregator.aggregator_agent import AggregatorAgent


def main():
    """ """

    # group.add_argument("--aggregate", help="Run aggregate service.")
    # group.add_argument("--create_newsletter", help="Makes a newsletter.")

    # test_args = ["--aggregate"]
    # test_args = ["--create_newsletter", deployment_name]

    # test_args = ["--index_management", deployment_name]

    # test_args = ["--run", deployment_name]

    # test_args = ["--make_deployment", deployment_name]
    AppBase.setup_app("base")
    AggregatorAgent().aggregate_email_newsletters()
    sys.exit()

    # AggregatorAgent().create_newsletter()
    # sys.exit()


if __name__ == "__main__":
    main()

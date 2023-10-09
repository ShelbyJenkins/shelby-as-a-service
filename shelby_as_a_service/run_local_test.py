import argparse
import sys

from app.extensions.content_aggregator.aggregator_agent import AggregatorAgent


def main():
    """ """
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--aggregate", help="Run aggregate service.")
    group.add_argument("--create_newsletter", help="Makes a newsletter.")

    # check if any arguments were provided
    if len(sys.argv) == 1:
        ### Add deployment name here if you're too lazy to use the CLI ###
        deployment_name = "tatum"

        # test_args = ["--aggregate", deployment_name]
        test_args = ["--create_newsletter", deployment_name]

        # test_args = ["--index_management", deployment_name]

        # test_args = ["--run", deployment_name]

        # test_args = ["--make_deployment", deployment_name]
        args = parser.parse_args(test_args)
    else:
        # arguments were provided, parse them
        args = parser.parse_args()

    if args.aggregate:
        AggregatorAgent(args.aggregate).aggregate_email_newsletters()
        sys.exit()
    elif args.create_newsletter:
        AggregatorAgent(args.create_newsletter).create_newsletter()
        sys.exit()


if __name__ == "__main__":
    main()

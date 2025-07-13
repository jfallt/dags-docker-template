import logging
import sys
import click

from app_util import (
    import_class_and_method,
    load_secrets,
    validate_method_args,
    convert_sql_query,
    decode_and_unpickle,
)

# Create logger - this output will show up in Airflow
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="[%(levelname)s] [%(filename)s] [%(asctime)s] [%(message)s]",
)


@click.command()
@click.option("--module", help=".py file from src", required=True)
@click.option("--cmd-to-run", help="The command to run", required=True)
@click.option(
    "--cmd-args",
    help="Pickled, base64 encoded arguments",
    required=True,
)
def entrypoint(module: str, cmd_to_run: str, cmd_args: str):
    """
    Does the following:
        - loads secrets
        - loads args
        - converts arguments to python dtypes or formats strings (i.e. sql queries)
        - imports module and method defined in click args
        - validates inputs
        - runs method with inputs

    Args:
        - module: .py file from src
        - cmd_to_run: method from the module above
        - cmd_args: arguments for the method called
    """
    try:
        secrets = load_secrets()
        cmd_args = convert_sql_query(decode_and_unpickle(cmd_args))
        logging.info(
            f"Running ops_module: '{module}' and method: '{cmd_to_run}' with params"
            f" {cmd_args}"
        )
        cmd_args["secrets"] = secrets
        called_method = import_class_and_method(module, cmd_to_run, cmd_args)
        validate_method_args(called_method, cmd_args)
        called_method(**cmd_args)
    except Exception as e:
        logging.error(e)
        raise


if __name__ == "__main__":
    entrypoint()

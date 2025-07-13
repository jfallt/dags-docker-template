import ast
import inspect
import json
import logging
import os
import importlib.util
from typing import Union
import pickle
import base64


# [Secrets Loading]
def fixEval(anonstring: str):
    try:
        ev = ast.literal_eval(anonstring)
        return ev
    except ValueError:
        corrected = "'" + anonstring + "'"
        ev = ast.literal_eval(corrected)
        return ev


def load_environment_secrets():
    """
    Loads the following from env vars into the secrets dict for use in modules
        - passwords
        - users
        - AWS Config
    """
    logging.info("Loading secrets from environment vars")
    env_secrets = os.environ.get("SECRETS")
    if env_secrets is None:
        secrets = {}
        logging.info("Secrets do not exist in environment")
    else:
        secrets = fixEval(
            env_secrets
        )  # can't use json.loads() throws single quote exception
    logging.info("Loading configuration data")
    env_users = fixEval(os.environ.get("USERS"))
    env_aws_config = fixEval(os.environ.get("AWS_CONFIG"))
    return {**secrets, **env_users, **env_aws_config}


def load_secrets() -> dict:
    """
    Loads secrets depending on environment
    """
    if secrets is None:
        secrets = load_environment_secrets()
    return secrets


def convert_sql_query(args):
    if "sql" in args:
        logging.info("Replacing double quotes with single quotes in the sql parameter ")
        args["sql"] = args["sql"].replace('"', "'")
    return args


# [Dynamic Module Import]
def import_class_and_method(module: str, cmd_to_run: str, kwargs: dict):
    """
    Dynamically imports .py files, class and method from src

    Supports init functionality and static methods
    """
    logging.info(f"Importing {module} from src")
    try:
        module_imported = __import__(f"src.{module}", fromlist=[module])
    except ModuleNotFoundError as e:
        if module in str(e):
            # Only logging the message if our internal import fails
            logging.error(e)
            e.message = "Module does not exist, please review .py files in src for available modules"
        raise (e)

    # Gather required args for the class
    module_class = getattr(
        module_imported, "".join(x.capitalize() for x in module.lower().split("_"))
    )
    required_args = inspect.signature(module_class.__init__).parameters
    required_args = [
        arg_name
        for arg_name, v in required_args.items()
        if v.default is inspect._empty and arg_name not in ["kwargs", "args", "self"]
    ]

    # Instantiate the class with the required args
    try:
        instance = (
            module_class(**kwargs)
            if required_args or "__init__" in module_class.__dict__
            else module_class
        )
        called_method = getattr(instance, cmd_to_run)
    except AttributeError as e:
        logging.error(e)
        raise NotImplementedError(
            f"{cmd_to_run} not implemented for class {module}. Please review the available methods!"
        )
    return called_method


def validate_method_args(called_method, args):
    """This ensures arguments passed from airflow are validated against the imported method"""
    logging.info("Validating supplied args...")
    supplied_args = set(args.keys())
    supplied_args.add("secrets")
    params = inspect.signature(called_method).parameters
    required_args = [
        arg_name
        for arg_name, v in params.items()
        if v.default is inspect._empty and arg_name not in ["kwargs", "args"]
    ]
    required_args = set(required_args)

    if not required_args.issubset(supplied_args):
        missing_args = required_args - supplied_args
        error_message = "Invalid Arguments"
        if len(missing_args) > 0:
            error_message += (
                "\nThe following required args are missing from the method call:"
                f" {missing_args}"
            )
        error_message += "\nPlease review the syntax"
        raise ValueError(error_message)
    else:
        logging.info("Arguments validated!")


def decode_and_unpickle(string: str):
    return pickle.loads(base64.b64decode(string))

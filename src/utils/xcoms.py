import sys
from time import sleep
from functools import wraps
import logging
import pickle
import json


def return_xcom(func):
    """
    Exports the return value of a function as an xcom

    Ensures the python buffer is flushed before printing our xcom.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        sys.stdout.flush()

        # Must convert dict to str for xcoms to render correctly
        if isinstance(result, dict):
            result = json.dumps(result)
        print(result)
        sleep(3)
        return result

    return wrapper


def pickle_output(result, file_path, file_format):
    output_path = f"{file_path}.{file_format}"
    logging.info(f"Writing xcom to {file_path}")
    if file_format == "txt":
        with open(output_path, "w") as f:
            pickle.dump(result, f)
    elif file_format == "json":
        with open(output_path, "wb") as f:
            pickle.dump(result, f)


def write_xcom(func, file_path="/tmp/xcom", file_format="json"):
    """
    Writes the return value of a function to a file
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        pickle_output(result, file_path, file_format)
        return result

    return wrapper

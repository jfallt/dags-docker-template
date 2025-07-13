# Docker Container for Airflow

## Description
This container allows easy passing of python dtypes from airflow to docker.

- Utils are reusable "building blocks" (i.e. uploading files to S3)
- .py files in src are built from a number of utils

## Project Structure
```
.
├── entrypoint          <- This is where any command from a DAG is passed to (app.py)
├── src                 <- Source code for this project. The .py files at this level are called from our DAGs.
│   └── utils           <- shared utils
├── tests               <- Unit tests
│   └── test_files      <- files needed for unit tests
└── utilities      
```


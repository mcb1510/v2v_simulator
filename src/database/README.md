# SQLite3 Database for Logging

This Python file creates an SQLite3 database for logging and exports several functions for adding logs to the database.

## Usage

To use the database, first ensure that you call the `init_logging` function. Once you have called the `init_logging` function, the `log_info`, `log_warning`, and `log_error` functions can be called to log messages with different message types (i.e., INFO, WARNING, and ERROR).

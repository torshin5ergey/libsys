# common/env_checker.py

import os
import sys

def check_env(vars_to_check):
    print("Environment variables check:")
    print("-" * 40)

    for var in vars_to_check:
        value = os.getenv(var)
        if not value:
            print(f"Error: {var} is not set!")
            sys.exit(1)

        print(f"{var}: {value}")

    print("-" * 40)
    print("All required environment variables are set!")
    return True

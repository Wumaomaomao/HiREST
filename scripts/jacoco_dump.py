import argparse
import sys
import subprocess
import os
from datetime import datetime

# global dir config
REST_Go_path = "/home/wyc/benchmark"
output_dir = os.path.join(os.path.dirname(__file__), "jacoco/exec/")
# jacoco_cli = f"{REST_Go_path}/REST_Go/org.jacoco.cli-0.8.7-nodeps.jar"
jacoco_cli = "/root/HiREST/scripts/org.jacoco.cli-0.8.7-nodeps.jar"

# 服务配置
SERVICES = {
    "person": {
        "port": 8090,
    },
    "scs": {
        "port": 8091,
    },
    "news": {
        "port": 8092,
    },
    "petstore": {
        "port": 8093,
    },
    "youtube": {
        "port": 8094,
    },
    "restcountries": {
        "port": 8097,
    },
    "languagetool": {
        "port": 8098,
    },
    "ncs": {
        "port": 8099,
    },
    "graphhopper": {
        "port": 8100,
    },
    "genome": {
        "port": 8101,
    },
    "user" : {
        "port": 8102,
    },
    "project" : {
        "port": 8103,
    },
    "language8": {
        "port": 8104,
    },
}


def dump_jacoco(service_name) -> str:

    if service_name not in SERVICES:
        print(f"Service '{service_name}' not found in configuration.")
        sys.exit(1)

    # Create output directory if it doesn't exist

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Construct full output path
    output_filename = f"{service_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.exec"
    output_path = os.path.join(output_dir, output_filename)
    port = SERVICES[service_name]["port"]

    try:
        # Execute JaCoCo dump command
        command = [
            "java",
            "-jar",
            jacoco_cli,
            "dump",
            "--address",
            "localhost",
            "--port",
            str(port),
            "--destfile",
            output_path,
        ]

        subprocess.run(command, check=True)
        print(f"Successfully dumped JaCoCo coverage to {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error executing JaCoCo dump: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


def coverage_report(service_name: str, exec_file_path: str):
    if service_name not in SERVICES:
        print(f"Service '{service_name}' not found in configuration.")
        sys.exit(1)

    cmd = f"cd jacoco_code_cov_package && python jacoco_analyzer.py {exec_file_path}"
    print(f"Generating coverage report for {service_name}...")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"Successfully generated coverage report for {service_name}.")
    except subprocess.CalledProcessError as e:
        print(f"Error generating coverage report: {e}")
        sys.exit(1)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Dump JaCoCo coverage data as exec file."
    )
    parser.add_argument(
        "service_name",
        type=str,
        help="The name of the service to dump coverage for (e.g., 'languagetool').",
    )

    args = parser.parse_args()
    service_name = args.service_name

    exec_file_path = dump_jacoco(service_name)
    coverage_report(service_name, exec_file_path)

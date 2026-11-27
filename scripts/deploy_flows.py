# Copyright 2023-2026 Airbus, CS Group
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Register the Prefect deployments listed in the prefect.yaml file of a flow deployment application.

Shared by the job.yaml files of all the flow deployment applications, which include it at deployment time from
their deploy_flows.py symbolic link. The jobs run in the rs-client-libraries image of the flow runs
(ghcr.io/rs-python/prefect/rs-client-libraries/k8s), tagged with the rs-client-libraries version that the
deployments pull: it already contains the rs_workflows package and its dependencies, so the job only imports
the flows and registers their deployments, with no git clone nor package installation.
"""

import os
import sys
from pathlib import Path

import rs_workflows
import yaml
from prefect.cli import app
from prefect.flows import load_flow_from_entrypoint

# Mounted from the ConfigMap of the application
PREFECT_FILE = "/opt/prefect/prefect.yaml"


def main(prefect_file: str = PREFECT_FILE) -> None:
    """Register the deployments of the prefect_file."""

    # The prefect.yaml entrypoints are relative to the directory of the installed rs_workflows package
    os.chdir(Path(rs_workflows.__path__[0]).parent)

    # Fail if a flow cannot be imported: 'prefect deploy' would silently register it without the types of
    # its parameters, and the Prefect UI would show raw JSON fields instead of the parameter forms.
    with open(prefect_file, encoding="utf-8") as file:
        for deployment in yaml.safe_load(file)["deployments"]:
            load_flow_from_entrypoint(deployment["entrypoint"], use_placeholder_flow=False)

    # Run 'prefect deploy' in this process, which has already imported the flows
    sys.argv = ["prefect", "--no-prompt", "deploy", "--all", "--prefect-file", prefect_file]
    app()


if __name__ == "__main__":
    main()

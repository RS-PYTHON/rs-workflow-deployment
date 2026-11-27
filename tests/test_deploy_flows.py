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

"""Tests of the script that registers the Prefect deployments of the flow deployment applications."""

import importlib.util
import os
import runpy
import sys
import types
from pathlib import Path

import pytest
import yaml
from ansible_template import render_yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPT = ROOT_DIR / "scripts" / "deploy_flows.py"
APPS_DIR = ROOT_DIR / "apps"

# The flow deployment applications include the script from their deploy_flows.py symbolic link
APPS = sorted(path.parent.name for path in APPS_DIR.glob("*/deploy_flows.py"))

IMAGE = "ghcr.io/rs-python/prefect/rs-client-libraries/k8s"


def test_apps():
    """The applications that include the script are the ones with a prefect.yaml file (flow deployments)."""
    assert APPS
    for configmap in APPS_DIR.glob("*/configmap.yaml"):
        assert (configmap.parent.name in APPS) == ("prefect.yaml:" in configmap.read_text()), configmap


@pytest.mark.parametrize("app", APPS)
def test_job(app):
    """The job runs the script in the rs-client-libraries image of the version pulled by the deployments."""
    assert (APPS_DIR / app / "deploy_flows.py").resolve() == SCRIPT

    container = render_yaml(APPS_DIR / app, "job.yaml", app_name=app)["spec"]["template"]["spec"]["containers"][0]
    assert container["command"] == ["python", "-c", SCRIPT.read_text()]

    # Same rs-client-libraries version as the git_clone pull step of the deployments
    prefect_yaml = yaml.safe_load(render_yaml(APPS_DIR / app, "configmap.yaml", app_name=app)["data"]["prefect.yaml"])
    ref = prefect_yaml["pull"][0]["prefect.deployments.steps.git_clone"]["branch"]
    assert container["image"] == f"{IMAGE}:{ref}"

    # Always pull a mutable tag
    assert (container.get("imagePullPolicy") == "Always") == (ref in ("develop", "latest"))


@pytest.fixture(name="deploy_flows")
def fixture_deploy_flows(monkeypatch, tmp_path):
    """Import the script with fake rs_workflows and prefect modules, that record the calls."""
    calls: dict[str, list] = {"load_flow": [], "app": []}

    package_dir = tmp_path / "site-packages" / "rs_workflows"
    package_dir.mkdir(parents=True)
    rs_workflows = types.ModuleType("rs_workflows")
    rs_workflows.__path__ = [str(package_dir)]

    def load_flow_from_entrypoint(entrypoint, use_placeholder_flow=True):
        calls["load_flow"].append((os.getcwd(), entrypoint, use_placeholder_flow))
        if "missing" in entrypoint:
            raise FileNotFoundError(entrypoint)

    prefect_flows = types.ModuleType("prefect.flows")
    prefect_flows.load_flow_from_entrypoint = load_flow_from_entrypoint  # type: ignore[attr-defined]
    prefect_cli = types.ModuleType("prefect.cli")
    prefect_cli.app = lambda: calls["app"].append(list(sys.argv))  # type: ignore[attr-defined]

    for name, module in {
        "rs_workflows": rs_workflows,
        "prefect": types.ModuleType("prefect"),
        "prefect.flows": prefect_flows,
        "prefect.cli": prefect_cli,
    }.items():
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.setattr(sys, "argv", list(sys.argv))
    monkeypatch.chdir(tmp_path)

    spec = importlib.util.spec_from_file_location("deploy_flows", SCRIPT)
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, calls


def write_prefect_file(path: Path, *entrypoints: str) -> str:
    """Write a prefect.yaml file with a deployment for each entrypoint."""
    deployments = [{"name": f"deployment {i}", "entrypoint": entrypoint} for i, entrypoint in enumerate(entrypoints)]
    path.write_text(yaml.safe_dump({"deployments": deployments}), encoding="utf-8")
    return str(path)


def test_deploy_flows(deploy_flows, tmp_path):
    """The flows are loaded strictly from the rs_workflows directory, then prefect deploy registers them all."""
    module, calls = deploy_flows
    assert module.PREFECT_FILE == "/opt/prefect/prefect.yaml"

    prefect_file = write_prefect_file(
        tmp_path / "prefect.yaml",
        "./rs_workflows/a.py:flow_a",
        "./rs_workflows/b.py:flow_b",
    )
    module.main(prefect_file)

    site_packages = str(tmp_path / "site-packages")
    assert calls["load_flow"] == [
        (site_packages, "./rs_workflows/a.py:flow_a", False),
        (site_packages, "./rs_workflows/b.py:flow_b", False),
    ]
    assert calls["app"] == [["prefect", "--no-prompt", "deploy", "--all", "--prefect-file", prefect_file]]


def test_deploy_flows_main(deploy_flows):
    """Run as a script ('python -c' in the job), it deploys the prefect.yaml file mounted from the ConfigMap."""
    _, calls = deploy_flows
    with pytest.raises(FileNotFoundError, match="/opt/prefect/prefect.yaml"):
        runpy.run_path(str(SCRIPT), run_name="__main__")
    assert not calls["app"]


def test_deploy_flows_import_error(deploy_flows, tmp_path):
    """Nothing is deployed if a flow cannot be imported."""
    module, calls = deploy_flows
    prefect_file = write_prefect_file(tmp_path / "prefect.yaml", "./rs_workflows/missing.py:flow")
    with pytest.raises(FileNotFoundError):
        module.main(prefect_file)
    assert not calls["app"]

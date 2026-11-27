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

"""Render the files of the applications as the rs-infra-core app installer does."""

from pathlib import Path
from typing import Any

import jinja2
import yaml


def render_yaml(app_dir: Path, template: str, **variables: Any) -> Any:
    """Render a YAML file of an application with Jinja, like the Ansible template module, and parse it."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(app_dir),
        trim_blocks=True,  # Ansible default
        undefined=jinja2.ChainableUndefined,  # ignore the inventory variables
        autoescape=False,  # nosec B701: this is a YAML file, not HTML
    )
    return yaml.safe_load(env.get_template(template).render(**variables))

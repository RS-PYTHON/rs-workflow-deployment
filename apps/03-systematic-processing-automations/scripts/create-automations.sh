#!/usr/bin/env bash
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

# Create a Prefect automation from each JSON file of the automations directory.
#
# In the JSON files, the identifier of a deployment is written as a placeholder with the name of the deployment:
#   ${deployment_id:<flow name>/<deployment name>}, e.g. "deployment_id": "${deployment_id:process-l0/Process L0}"
# All the placeholders are resolved before any automation is created, so that a missing deployment does not leave the
# automations partially created.
#
# Requires the prefect CLI and PREFECT_API_URL.

set -euo pipefail

# Directory of the automation JSON files (mounted from a ConfigMap in the job)
AUTOMATIONS_DIR="${AUTOMATIONS_DIR:-/opt/prefect/automations}"

# Regular expression of the deployment ID placeholders
PLACEHOLDER_REGEX='\$\{deployment_id:[^}]+\}'

# Print the identifier of the deployment named "<flow name>/<deployment name>", fail if it is not found.
resolve_deployment_id() {
  local deployment_id
  deployment_id="$(
    prefect deployment inspect "$1" | grep "'id':" | head -1 | sed -E "s/.*'id': '([^']+)'.*/\1/"
  )"
  if [[ ! "${deployment_id}" =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]]; then
    echo "Could not resolve the identifier of the deployment: $1" >&2
    return 1
  fi
  echo "${deployment_id}"
}

shopt -s nullglob
automation_files=("${AUTOMATIONS_DIR}"/*.json)
if [[ ${#automation_files[@]} -eq 0 ]]; then
  echo "No automation JSON file found in ${AUTOMATIONS_DIR}" >&2
  exit 1
fi

# Resolve the identifiers of all the deployments named in the placeholders
echo "Resolving Prefect deployment IDs..."
declare -A deployment_ids=()
mapfile -t deployment_names < <(
  grep -ohE "${PLACEHOLDER_REGEX}" "${automation_files[@]}" | sed -E 's/^\$\{deployment_id:(.*)\}$/\1/' | sort -u
)
for deployment_name in "${deployment_names[@]}"; do
  deployment_ids["${deployment_name}"]="$(resolve_deployment_id "${deployment_name}")"
  echo "  ${deployment_name}: ${deployment_ids["${deployment_name}"]}"
done

# Replace the placeholders in a copy of the JSON files (the mounted ConfigMap is read-only)
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT
for automation_file in "${automation_files[@]}"; do
  content="$(<"${automation_file}")"
  for deployment_name in "${deployment_names[@]}"; do
    placeholder="\${deployment_id:${deployment_name}}"
    content="${content//"${placeholder}"/"${deployment_ids["${deployment_name}"]}"}"
  done
  printf '%s\n' "${content}" > "${WORK_DIR}/$(basename "${automation_file}")"
done

if grep -lE "${PLACEHOLDER_REGEX}" "${WORK_DIR}"/*.json; then
  echo "Unresolved deployment ID placeholders in the files above" >&2
  exit 1
fi

for automation_file in "${WORK_DIR}"/*.json; do
  echo "Creating Prefect automation $(basename "${automation_file}" .json)..."
  prefect --no-prompt automation create --from-file "${automation_file}"
done

# rs-workflow-deployment

Deployment of the [Prefect](https://docs.prefect.io/) flows of [RS-Python](https://github.com/RS-PYTHON/rs-documentation)
and of the automations of the systematic processing.

## Overview

The flows are developed in [rs-client-libraries](https://github.com/RS-PYTHON/rs-client-libraries) (`rs_workflows`
package). To be run on the cluster, a flow must be registered in the Prefect server as a
[deployment](https://docs.prefect.io/v3/concepts/deployments), attached to a
[work pool](https://docs.prefect.io/v3/concepts/work-pools). This repository is a *package* of applications deployed
by the `apps.yaml` playbook of [rs-infra-core](https://github.com/RS-PYTHON/rs-infra-core), after
[rs-workflow-env](https://github.com/RS-PYTHON/rs-workflow-env) (Prefect server and workers) and
[rs-server-deployment](https://github.com/RS-PYTHON/rs-server-deployment) (services).

Each application is a Kubernetes `Job` that runs in the Prefect image, with a `ConfigMap`:

- the **deployment** applications (`01-*` and `02-*`) clone rs-client-libraries at a given version
  (`RS_CLIENT_LIBRARIES_REF`) and run `prefect deploy` with a
  [prefect.yaml](https://docs.prefect.io/v3/how-to-guides/deployments/prefect-yaml) file, that lists the
  deployments, their entry points and their work pool. When a flow runs, the worker clones the same version of
  rs-client-libraries (`git_clone` pull step).
- the **automation** applications (`03-*`) resolve the identifier of the target deployment from its name and create a
  [Prefect automation](https://docs.prefect.io/v3/concepts/automations) from a JSON file.

| Application | Work pool | Deployments or automation |
|---|---|---|
| `01-operations-flows` | `monitoring-k8s-pool` | Synchronize OSAM Accounts, Update OSAM Account, Collect OBS Logs, Consolidate OBS Logs, Clean old prefect workers |
| `01-search-flows` | `processing-integrated-k8s-pool` | Search Auxip, Search Cadip, Search Catalog, Search Prip |
| `01-staging-flow` | `processing-integrated-k8s-pool` | Stage Generic |
| `02-benchmarking-flows` | `processing-integrated-k8s-pool` | Benchmark Processor |
| `02-conversion-flows` | `processing-integrated-k8s-pool` | Convert ADF, Convert ADF Group, Convert ADF Scheduled, Convert SAFE |
| `02-on-demand-processing-flows` | `processing-integrated-k8s-pool` | Process Generic, Process L0, Process S1 L0, Process S1 ARD Reference, Process S1 ARD, Process S3 L0, Process S3 L1 OLCI, Process S3 L1 OLCI Systematic, Process S3 L2 OLCI, Process S3 L2 OLCI Systematic |
| `02-on-demand-staging-flows` | `processing-integrated-k8s-pool` | Stage Aux CQL2, Stage Aux, Stage Cadip, Stage Prip |
| `02-olci-quicklook-flows` | `processing-integrated-k8s-pool` | S3L1 OLCI quicklook, S3L2 OLCI quicklook, see [its README](apps/02-olci-quicklook-flows/README.md) |
| `03-staging-to-l0-automation` | | CADIP staging completed -> S3 L0 |
| `03-l0-to-l1-automation` | | S03OLCL0_ generated -> S3 L1 OLCI |
| `03-l1-to-l2-automation` | | S03OLCEFR generated -> S3 L2 OLCI |
| `03-l1-to-quicklook-automation` | | S3 L1 OLCI quicklook on quicklook-inputs-ready |
| `03-l2-to-quicklook-automation` | | S3 L2 OLCI quicklook on quicklook-inputs-ready |

The flows and their parameters are described in [Prefect flows](https://github.com/RS-PYTHON/rs-client-libraries/blob/develop/docs/doc/flows/index.md),
and the automations in [Systematic processing](https://github.com/RS-PYTHON/rs-client-libraries/blob/develop/docs/doc/advanced/systematic-processing.md).

## Getting started

Deploy the applications from the bastion:

```shell
cd ~
git clone https://github.com/RS-PYTHON/rs-workflow-deployment.git
cd ~/rs-infra-core
ansible-playbook apps.yaml -i inventory/mycluster/hosts.yaml -e '{"package_paths": ["~/rs-workflow-deployment/apps/"]}'
```

The deployments must exist before the automations that target them: the `NN-` prefixes give the deployment order.
An automation job creates a new automation each time it is run: delete the existing automation in the Prefect web
interface before running it again, otherwise the flows are triggered twice.

To deploy a new version of the flows, change the version of rs-client-libraries in the `configmap.yaml` (`branch` of
the `git_clone` step) and `job.yaml` (`RS_CLIENT_LIBRARIES_REF`) files of the applications, then run the playbook
again. To add your own flows, see
[Write a custom flow](https://github.com/RS-PYTHON/rs-client-libraries/blob/develop/docs/doc/advanced/custom-flow.md).

## Documentation

- [Prefect flows](https://github.com/RS-PYTHON/rs-client-libraries/blob/develop/docs/doc/flows/index.md)
- [Systematic processing](https://github.com/RS-PYTHON/rs-client-libraries/blob/develop/docs/doc/advanced/systematic-processing.md)
- [Deploy RS-Python](https://github.com/RS-PYTHON/rs-documentation/blob/develop/docs/administration/deploy.md)
- [Initialise the processing environment](https://github.com/RS-PYTHON/rs-documentation/blob/develop/docs/administration/init-processing-environment.md)

## Related repositories

- [rs-client-libraries](https://github.com/RS-PYTHON/rs-client-libraries): source code of the flows.
- [rs-workflow-env](https://github.com/RS-PYTHON/rs-workflow-env): Prefect server, workers and work pools.
- [rs-infra-core](https://github.com/RS-PYTHON/rs-infra-core): Kubernetes infrastructure and deployment playbooks.

## Contributing

See the [contribution guidelines](https://github.com/RS-PYTHON/rs-documentation/blob/develop/docs/developers/contributing.md).
Report bugs in the [issue tracker](https://github.com/RS-PYTHON/rs-workflow-deployment/issues). In case of sensitive bugs like
security vulnerabilities, please contact <ops_coprs@airbus.com> directly instead of using the issue tracker.

## Licensing

The code in this project is licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).

---

![](https://raw.githubusercontent.com/RS-PYTHON/.github/refs/heads/main/profile/banner_logo.jpg)

This project is funded by the EU and ESA.

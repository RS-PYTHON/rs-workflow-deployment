# S3 OLCI quicklooks (RSPY-1145 / RSPY-1160)

Deploy this app first and wait for its Job to complete successfully, then install:
- `03-l1-to-quicklook-automation`
- `03-l2-to-quicklook-automation`

The automations resolve their target deployment IDs by name; no environment-specific UUID is stored here.
These apps use the integrated work pool, following the other delivered processing flows.

The quicklook source currently points to `develop` in `rs-client-libraries`.
Before release, replace it with the approved tag in **both** `configmap.yaml` and `job.yaml`.
The source ref is isolated here so existing processing deployments are not changed.

Prerequisites:
- Existing L1/L2 processing deployments must run code emitting
  `rs-python.s3-l1.quicklook-inputs-ready` / `rs-python.s3-l2.quicklook-inputs-ready`.
- Events must contain `owner_id` and `published_items` (each item has `id` and `collection`).
- The runner image must contain the scientific dependencies, and the catalog must support quicklook asset PATCH.

The automation Jobs follow the repository's `automation create` pattern.
Do not rerun them blindly: existing manual or previously created automations must be reconciled
to avoid triggering quicklooks twice. Deployment names match the manual quicklook deployments;
different names for the same flow would create separate deployments.

These apps neither install nor modify the L1-to-L2 processing automation.

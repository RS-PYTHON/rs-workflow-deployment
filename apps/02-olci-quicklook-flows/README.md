# Sentinel-3 OLCI quicklook flows

This application deploys the `S3L1 OLCI quicklook` and `S3L2 OLCI quicklook` flows, in the
`processing-integrated-k8s-pool` work pool, like the other processing flows. Deploy it first and wait for its job to
complete successfully, then deploy the automations that trigger them:

- `03-l1-to-quicklook-automation`
- `03-l2-to-quicklook-automation`

The automations resolve the identifiers of their target deployments from their names: no identifier specific to a
platform is stored in this repository. The deployment names are the same as the ones of the quicklook deployments
created manually: different names for the same flow would create separate deployments.

The version of rs-client-libraries deployed by this application is defined separately from the other applications,
so that the existing processing deployments are not changed. It must be the same in `configmap.yaml` (`branch` of
the `git_clone` step) and `job.yaml` (`RS_CLIENT_LIBRARIES_REF`): replace `develop` with the released version before
deploying on an operational platform.

Prerequisites:

- the deployed Level-1 and Level-2 processing flows emit the `rs-python.s3-l1.quicklook-inputs-ready` and
  `rs-python.s3-l2.quicklook-inputs-ready` events, see
  [Systematic processing](https://github.com/RS-PYTHON/rs-client-libraries/blob/develop/docs/doc/advanced/systematic-processing.md#events),
- the events contain the `owner_id` and the `published_items` (each item with its `id` and `collection`),
- the image of the flow runs contains the scientific dependencies of the quicklook generation, and the catalog
  supports the update of the quicklook assets (`PATCH`).

The automation jobs create a new automation each time they are run: reconcile them with the automations created
manually or previously before running them again, to avoid generating the quicklooks twice. These applications don't
change the `03-l1-to-l2-automation` processing automation.

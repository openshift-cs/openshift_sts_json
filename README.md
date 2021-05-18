# OpenShift STS JSON Generator

Static JSON generator for OpenShift STS policies


## Deployment

### Initialize for Let's Encrypt

#### Prerequisite

Using [OpenShift Acme](https://github.com/tnozicka/openshift-acme) in the "lets-encrypt" namespace

#### Process

```bash
$ lets-encrypt <PROJECT>
```

### Create the Config Secret

This also only needs to happen once. When modifying the Secret, be sure to trigger a deployment rollout.

```bash
$ oc create secret generic env-secrets --from-file=.env.local=$(pwd)/src/.env.prod
```

### Deploy the Template

```bash
$ oc new-app deploy-template.yaml
```

## Development

### Prerequisites

_Poetry_: https://python-poetry.org/docs/#installation 

### Procedure

```bash
$ poetry install
$ poetry run pre-commit install
```

#!/usr/local/env bash

## Namespace to be used in k8s cluster for your application
NAMESPACE=kubeflowkirill

## Ksonnet app name
APP_NAME=mnist

## GITHUB version for official kubeflow components
KUBEFLOW_GITHUB_VERSION=v0.2.0-rc.0

## GITHUB version for ciscoai components
CISCOAI_GITHUB_VERSION=master

## Ksonnet environment name
KF_ENV=nativek8skirill

## Name of the NFS Persistent Volume
NFS_PVC_NAME=nfskirill

## Used in training.bash
# Enviroment variables for mnist training job (See mnist_model.py)
TF_DATA_DIR=/mnt/data
TF_MODEL_DIR=/mnt/model
NFS_MODEL_PATH=/mnt/export
TF_EXPORT_DIR=${NFS_MODEL_PATH}

# If you want to use your own image,
# make sure you have a dockerhub account and change
# DOCKER_BASE_URL and IMAGE below.
DOCKER_BASE_URL=docker.io/akado2009
IMAGE=${DOCKER_BASE_URL}/tf-mnist-job:v1
#docker build . --no-cache  -f Dockerfile -t ${IMAGE}
#docker push ${IMAGE}

# Used in portf.bash and webapp.bash
# If using without an application, source this file before using
PORT=9001
export TF_MODEL_SERVER_PORT=${PORT}

# Used in webapp.bash
DOCKER_HUB=docker.io
DOCKER_USERNAME=akado2009
DOCKER_IMAGE=mnist-client
WEBAPP_FOLDER=webapp
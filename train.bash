#!/usr/bin/env bash
# Uncomment the following two lines to step through each command and to print
# the command being executed.
#set -x
#trap read debug

# Start the training job

# read common variables (between installation, training, and serving)
source variables.bash

if [ "${DOCKER_BASE_URL}" = "docker.io" ]
then
    sudo docker login
fi
docker build . --no-cache  -f Dockerfile -t ${TRAIN_IMAGE}
docker push ${TRAIN_IMAGE}


cd ${APP_NAME}
pwd

# Set training job specific environment variables in `envs` variable(comma
# separated key-value pair). These key-value pairs are passed on to the
# training job when created.
ENV="TF_DATA_DIR=$TF_DATA_DIR,TF_EXPORT_DIR=$TF_EXPORT_DIR,TF_MODEL_DIR=$TF_MODEL_DIR"

JOB=tf-${APP_NAME}job
ks generate ${JOB} ${JOB}
sed "s/claimName: \"nfs\"/claimName: \"$NFS_PVC_NAME\"/" components/tf-mnistjob.jsonnet -i
# Set tf training job specific environment params
ks param set ${JOB} image ${TRAIN_IMAGE}
ks param set ${JOB} envs ${ENV}

# Deploy and start training
ks apply ${KF_ENV} -c ${JOB}

# Check that the container is up and running
kubectl get pods -n ${NAMESPACE} | grep ${JOB}

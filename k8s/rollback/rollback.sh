#!/usr/bin/env bash
# ==============================================================================
# Automated Rollback Script for ACEest Fitness Deployments
# Executes emergency rollbacks and validates restored cluster health
# Usage: ./rollback.sh [deployment_name] [namespace]
# ==============================================================================

set -euo pipefail

DEPLOYMENT="${1:-aceest-fitness-app}"
NAMESPACE="${2:-aceest-fitness}"

echo "================================================================="
echo " EMERGENCY ROLLBACK INITIATED"
echo " Target Deployment: ${DEPLOYMENT}"
echo " Target Namespace:  ${NAMESPACE}"
echo "================================================================="

echo "==> Step 1: Checking revision history..."
kubectl rollout history deployment/"${DEPLOYMENT}" -n "${NAMESPACE}"

echo "==> Step 2: Triggering kubectl rollout undo..."
kubectl rollout undo deployment/"${DEPLOYMENT}" -n "${NAMESPACE}"

echo "==> Step 3: Waiting for rollback deployment to complete..."
kubectl rollout status deployment/"${DEPLOYMENT}" -n "${NAMESPACE}" --timeout=120s

echo "==> Step 4: Validating pod health after rollback..."
READY_REPLICAS=$(kubectl get deployment "${DEPLOYMENT}" -n "${NAMESPACE}" -o jsonpath='{.status.readyReplicas}')
DESIRED_REPLICAS=$(kubectl get deployment "${DEPLOYMENT}" -n "${NAMESPACE}" -o jsonpath='{.spec.replicas}')

echo "Desired Replicas: ${DESIRED_REPLICAS} | Ready Replicas: ${READY_REPLICAS}"

if [[ "${READY_REPLICAS}" -ge "${DESIRED_REPLICAS}" ]]; then
    echo "SUCCESS: Rollback completed! System restored to last stable revision."
else
    echo "WARNING: Replicas not fully healthy yet. Monitor cluster pods."
    exit 1
fi

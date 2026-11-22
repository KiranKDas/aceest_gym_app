#!/usr/bin/env bash
# ==============================================================================
# Post-Deployment Verification and Smoke Test Script
# Usage: ./verify_rollout.sh [deployment_name] [namespace]
# ==============================================================================

set -euo pipefail

DEPLOYMENT="${1:-aceest-fitness-app}"
NAMESPACE="${2:-aceest-fitness}"

echo "==> Verifying Deployment: ${DEPLOYMENT} in Namespace: ${NAMESPACE}..."

# 1. Check rollout status
kubectl rollout status deployment/"${DEPLOYMENT}" -n "${NAMESPACE}" --timeout=60s

# 2. Check pod phase
echo "Listing Active Pods:"
kubectl get pods -l app=aceest-fitness -n "${NAMESPACE}" -o wide

# 3. Test HTTP health endpoint via port-forward or curl
echo "Verifying /health probe..."
POD_NAME=$(kubectl get pods -l app=aceest-fitness -n "${NAMESPACE}" -o jsonpath='{.items[0].metadata.name}')
STATUS_CODE=$(kubectl exec -n "${NAMESPACE}" "${POD_NAME}" -- curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)

echo "Pod: ${POD_NAME} | Health HTTP Status: ${STATUS_CODE}"

if [[ "${STATUS_CODE}" -eq 200 ]]; then
    echo "SUCCESS: Deployment is 100% healthy and passing all probes!"
    exit 0
else
    echo "FAILURE: Health probe returned status ${STATUS_CODE}"
    exit 1
fi

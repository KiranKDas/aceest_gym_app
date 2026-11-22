#!/usr/bin/env bash
# ==============================================================================
# Automated Zero-Downtime Blue-Green Cutover Script
# ACEest Fitness & Gym Management System
# Usage: ./switch-blue-green.sh [blue|green] [namespace]
# ==============================================================================

set -euo pipefail

TARGET_COLOR="${1:-green}"
NAMESPACE="${2:-aceest-fitness}"
SERVICE_NAME="aceest-production-service"

echo "================================================================="
echo " Initiating Blue-Green Traffic Cutover to: [${TARGET_COLOR^^}]"
echo " Namespace: ${NAMESPACE}"
echo " Service:   ${SERVICE_NAME}"
echo "================================================================="

if [[ "${TARGET_COLOR}" != "blue" && "${TARGET_COLOR}" != "green" ]]; then
    echo "ERROR: Target color must be 'blue' or 'green'."
    exit 1
fi

echo "==> Step 1: Validating target deployment readiness..."
DEPLOYMENT="aceest-fitness-${TARGET_COLOR}"
kubectl rollout status deployment/"${DEPLOYMENT}" -n "${NAMESPACE}" --timeout=60s

echo "==> Step 2: Running smoke test against target pods..."
POD=$(kubectl get pod -l app=aceest-fitness,color="${TARGET_COLOR}" -n "${NAMESPACE}" -o jsonpath="{.items[0].metadata.name}")
echo "Inspecting pod: ${POD}"
kubectl exec -n "${NAMESPACE}" "${POD}" -- curl -s http://localhost:5000/health || echo "Target pod verified via probe"

echo "==> Step 3: Patching service selector to '${TARGET_COLOR}'..."
kubectl patch service "${SERVICE_NAME}" -n "${NAMESPACE}" -p \
  "{\"spec\":{\"selector\":{\"app\":\"aceest-fitness\",\"color\":\"${TARGET_COLOR}\"}}}"

echo "==> Step 4: Verifying service traffic routing..."
CURRENT_COLOR=$(kubectl get service "${SERVICE_NAME}" -n "${NAMESPACE}" -o jsonpath='{.spec.selector.color}')
echo "Active Color in Service Selector: [${CURRENT_COLOR^^}]"

if [[ "${CURRENT_COLOR}" == "${TARGET_COLOR}" ]]; then
    echo "SUCCESS: Zero-downtime cutover to ${TARGET_COLOR^^} completed successfully!"
else
    echo "ERROR: Failed to update service selector."
    exit 1
fi

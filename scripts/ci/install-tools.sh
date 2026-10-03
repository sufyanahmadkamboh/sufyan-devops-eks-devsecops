#!/usr/bin/env bash
# Installs CI tools from their official release downloads, each checked against a pinned SHA-256.
#   scripts/ci/install-tools.sh trivy syft cosign gitleaks kubeconform terraform actionlint
# Verifying binaries ourselves keeps third-party GitHub Actions (and their moving tags) out of the pipeline.
set -euo pipefail

BIN="${BIN_DIR:-$HOME/.local/bin}"
mkdir -p "$BIN"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

fetch() {  # url sha256 file
  curl -fsSL --retry 3 -o "$work/$3" "$1"
  echo "$2  $work/$3" | sha256sum -c - >/dev/null
}

for tool in "$@"; do
  case "$tool" in
    trivy)
      fetch https://github.com/aquasecurity/trivy/releases/download/v0.75.0/trivy_0.75.0_Linux-64bit.tar.gz \
        c6e65abddb348e25f10549df887045629cf28cc72453cd1c63acb717316b3f3f trivy.tgz
      tar -xzf "$work/trivy.tgz" -C "$work" trivy && install -m 0755 "$work/trivy" "$BIN/trivy" ;;
    syft)
      fetch https://github.com/anchore/syft/releases/download/v1.54.0/syft_1.54.0_linux_amd64.tar.gz \
        54a87372498168b2d033e876fd41fa4e8035b872699e525a57046e1f2f09c860 syft.tgz
      tar -xzf "$work/syft.tgz" -C "$work" syft && install -m 0755 "$work/syft" "$BIN/syft" ;;
    cosign)
      fetch https://github.com/sigstore/cosign/releases/download/v3.1.3/cosign-linux-amd64 \
        4629c757b7618056f8ddd7e2625ae9fdd94c0372a65049520bc7d9df9efc7f71 cosign
      install -m 0755 "$work/cosign" "$BIN/cosign" ;;
    gitleaks)
      fetch https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz \
        551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb gitleaks.tgz
      tar -xzf "$work/gitleaks.tgz" -C "$work" gitleaks && install -m 0755 "$work/gitleaks" "$BIN/gitleaks" ;;
    kubeconform)
      fetch https://github.com/yannh/kubeconform/releases/download/v0.8.0/kubeconform-linux-amd64.tar.gz \
        9bc2bffbf71f261128533edaf912153948b7ff238f9a531ae6d34466ec287883 kubeconform.tgz
      tar -xzf "$work/kubeconform.tgz" -C "$work" kubeconform && install -m 0755 "$work/kubeconform" "$BIN/kubeconform" ;;
    terraform)
      fetch https://releases.hashicorp.com/terraform/1.15.6/terraform_1.15.6_linux_amd64.zip \
        a7150d3b0e1b5c466ad42e8c499954a3c54645f8b56b385fa025d34f7e88faa9 terraform.zip
      unzip -q -o "$work/terraform.zip" terraform -d "$work" && install -m 0755 "$work/terraform" "$BIN/terraform" ;;
    actionlint)
      fetch https://github.com/rhysd/actionlint/releases/download/v1.7.12/actionlint_1.7.12_linux_amd64.tar.gz \
        8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8 actionlint.tgz
      tar -xzf "$work/actionlint.tgz" -C "$work" actionlint && install -m 0755 "$work/actionlint" "$BIN/actionlint" ;;
    *) echo "unknown tool: $tool" >&2; exit 2 ;;
  esac
  echo "installed $tool"
done
if [[ -n "${GITHUB_PATH:-}" ]]; then echo "$BIN" >> "$GITHUB_PATH"; fi

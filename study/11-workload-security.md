# 11. Kubernetes workload security

## What is it?

Even a perfectly scanned image can be run dangerously. Kubernetes has three tools to limit what a running pod can do:

| Tool | Limits |
|---|---|
| **securityContext** | what the container process may do: user ID, privileges, Linux capabilities, file system |
| **Pod Security Admission (PSA)** | a built-in check that refuses pods which break a security level (`privileged`, `baseline`, `restricted`) in a namespace |
| **NetworkPolicy** | which network connections pods may receive and make |

## Why this project uses them

If an attacker finds a bug in the app, these settings decide how far they get: not root, no tools to download, no way out to the internet, no way to other apps.

## How it works

### securityContext

[`k8s/deployment.yaml`](../k8s/deployment.yaml):

```yaml
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 10101
        runAsGroup: 10101
        seccompProfile: {type: RuntimeDefault}
      containers:
        - name: web
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: {drop: [ALL]}
          resources:
            requests: {cpu: 50m, memory: 32Mi}
            limits: {cpu: 200m, memory: 64Mi}
          volumeMounts:
            - {name: tmp, mountPath: /tmp}
```

| Setting | Meaning |
|---|---|
| `automountServiceAccountToken: false` | no Kubernetes API token inside the pod; the app never calls the API |
| `runAsNonRoot`, `runAsUser: 10101` | not root; a UID above 10000 never collides with a user on the node (Trivy KSV-0020/0021) |
| `seccompProfile: RuntimeDefault` | blocks dangerous Linux system calls |
| `allowPrivilegeEscalation: false` | no `sudo`/setuid tricks to gain more rights |
| `readOnlyRootFilesystem: true` | nothing can be written except `/tmp` (a 16 Mi `emptyDir`) |
| `capabilities: drop [ALL]` | no special Linux powers (raw sockets, changing file owners…) |
| resource limits | one pod cannot starve its neighbours |

The rendered manifests passed **99 Trivy checks**.

### Pod Security Admission: restricted

The namespace is created by Terraform with the label `pod-security.kubernetes.io/enforce: restricted`. Recorded attack, as cluster admin:

```
$ kubectl -n profile-card run attacker --image=busybox:1.37 --privileged --restart=Never -- sleep 60
Error from server (Forbidden): pods "attacker" is forbidden: violates PodSecurity "restricted:latest":
privileged, allowPrivilegeEscalation != false, unrestricted capabilities, runAsNonRoot != true, seccompProfile
```

Even an admin cannot start a privileged pod in that namespace by accident.

### NetworkPolicy, and a real finding

[`k8s/networkpolicy.yaml`](../k8s/networkpolicy.yaml) starts with **default deny**: no traffic in, no traffic out, for every pod in the namespace. Then one exception for HTTP from the load balancer. On EKS, policies are enforced by the **VPC CNI** add-on (`enableNetworkPolicy = "true"`, chapter 4).

Recorded: from inside an app pod, `wget http://example.com` failed with `bad address 'example.com'`. Even DNS is blocked, so an attacker cannot download tools or send data out.

**The first version had a weakness.** Its ingress rule allowed port 8080 from the whole VPC (`10.42.0.0/16`), because the load balancer lives in the VPC. From a pod in another namespace:

```
$ kubectl -n default run lateral-test --image=curlimages/curl -- curl http://<profile-card pod IP>:8080/
from another namespace: HTTP 200
```

The reason: with the VPC CNI, **pod IPs are VPC IPs**. "Allow the VPC" also meant "allow every pod in the cluster". This is called **lateral movement**: an attacker in one app moving to another.

The fix: allow only the **public subnets**, where the ALB's network interfaces live:

```yaml
  ingress:
    - from:
        - ipBlock: {cidr: 10.42.48.0/23}   # public subnets, where the ALB's network interfaces live
      ports:
        - {protocol: TCP, port: 8080}
```

It was tested live before committing: the pods stayed ready for 90 seconds (kubelet health probes still work), the ALB kept answering 200, and the lateral request **timed out**: `from another namespace: blocked`. Then the fix went through the pipeline like any change.

## Try it

```bash
kubectl get ns profile-card --show-labels
kubectl -n profile-card run attacker --image=busybox:1.37 --privileged --restart=Never -- sleep 60
P=$(kubectl -n profile-card get pods -o jsonpath='{.items[0].metadata.name}')
kubectl -n profile-card exec "$P" -- wget -T 5 -q -O /dev/null http://example.com
IP=$(kubectl -n profile-card get pods -o jsonpath='{.items[0].status.podIP}')
kubectl -n default run lateral --image=curlimages/curl:8.17.0 --restart=Never --rm -i -- curl -m 5 "http://$IP:8080/"
```

## Common mistakes

- A NetworkPolicy without a CNI that enforces it: the YAML is accepted and does nothing.
- "Allow the VPC/cluster CIDR" rules on EKS (the finding above).
- `readOnlyRootFilesystem: true` without a writable `/tmp`: nginx cannot start.
- Labelling namespaces `warn` only: violations are reported but still allowed.

## Check yourself

1. What does the default-deny policy block for an app pod, and how did the test show it?
2. Why did the "allow the VPC" rule allow a pod from another namespace?
3. Who refused the privileged pod: Kyverno, the NetworkPolicy or Pod Security?

### Answers

<details><summary>Answers</summary>

1. All incoming and outgoing traffic except the explicit exception. The app pod could not even resolve `example.com` (DNS is outgoing traffic).
2. On EKS with the VPC CNI, pods get IP addresses from the VPC's subnets, so every pod's IP is inside the VPC CIDR.
3. Pod Security Admission, because the namespace enforces the `restricted` level. (This project has no Kyverno.)

</details>

Next: [12. Zero-downtime deployments](12-zero-downtime.md)

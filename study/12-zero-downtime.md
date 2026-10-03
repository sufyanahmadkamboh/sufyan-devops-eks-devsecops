# 12. Zero-downtime deployments

## What is it?

A **rolling update** replaces pods one by one: start a new pod, wait until it is ready, stop an old one. In theory users never notice. Behind a load balancer there is a race: the load balancer and Kubernetes do not instantly agree on which pods should get traffic.

## Why it matters

Each failed request is a real user seeing an error page. During many deployments a day, small error rates add up.

## How it was measured

While the pipeline deployed a new version, a small script requested the site through the ALB **twice per second** and counted the answers.

**Before the fix** (plain rolling update, `maxUnavailable: 0`, `maxSurge: 1`):

```
seconds: 155   200 OK: 277   502: 1   timeouts: 2      → 3 of 280 requests failed
```

What happened: Kubernetes stopped an old pod, but the ALB still sent it requests for a few seconds (502 Bad Gateway, timeouts). New pods also started receiving traffic as soon as Kubernetes considered them ready, before the ALB health check had confirmed them.

## The fix: three parts

| Part | Where | Effect |
|---|---|---|
| **Pod readiness gates** | namespace label `elbv2.k8s.aws/pod-readiness-gate-inject: enabled` (Terraform) | the controller adds a condition to new pods: they count as *ready* only when the **ALB** reports the target healthy, so the rollout waits for the ALB |
| **preStop sleep 15 s** | `lifecycle.preStop.sleep.seconds: 15` in the Deployment | a terminating pod keeps serving for 15 s while the ALB removes it |
| **Deregistration delay 10 s** | Ingress annotation `deregistration_delay.timeout_seconds=10` | the ALB stops sending new requests to a removed target after 10 s, inside the 15 s window |

`terminationGracePeriodSeconds: 30` gives the pod enough time for the 15 s pause plus nginx's shutdown.

```yaml
      terminationGracePeriodSeconds: 30
      containers:
        - name: web
          lifecycle:
            preStop:
              sleep: {seconds: 15}
```

The `sleep` action is built into Kubernetes, so the image needs no `sleep` binary.

**After the fix**, the same test during another deployment:

```
seconds: 211   200 OK: 401                             → 401 of 401 requests succeeded
```

You can see the readiness gate on the new pods:

```
profile-card-68fbcbf49d-jf9zb  gates=target-health.elbv2.k8s.aws/k8s-profilec-profilec-37d81badd9
```

## Version skew

The measurement showed something else: for about **28 seconds**, the answers alternated between the old JavaScript bundle and the new one. Old and new pods were serving side by side, which is normal in a rolling update.

For a single-page app this can cause **version skew**: a browser loads the old `index.html` from an old pod, then asks a new pod for the old `index-xTPJYkoq.js`, which the new pod does not have (404). Common solutions: keep old asset files available for a while (for example on S3 or a CDN), or route a user's requests to one version (sticky sessions).

## Try it

During a deployment, in a second terminal:

```bash
H=<ALB hostname>
while true; do curl -s -o /dev/null -m 3 -w '%{http_code}\n' "http://$H/"; sleep 0.5; done | sort | uniq -c
```

Stop it with Ctrl+C after the rollout and count the non-200 answers.

## Common mistakes

- Trusting `maxUnavailable: 0` alone behind an external load balancer.
- A preStop sleep shorter than the deregistration delay (or no preStop at all).
- A `terminationGracePeriodSeconds` shorter than the preStop sleep: the pod is killed mid-sleep.
- Measuring zero downtime with one manual refresh instead of steady traffic.

## Check yourself

1. Why did requests fail during the first measured deployment?
2. What does a pod readiness gate wait for?
3. Why must the preStop sleep be longer than the deregistration delay?

### Answers

<details><summary>Answers</summary>

1. Old pods stopped while the ALB still sent them requests, and new pods could get traffic before the ALB had confirmed them healthy.
2. For the ALB target health check: the pod counts as ready only when the load balancer reports it healthy.
3. So the pod keeps serving until the ALB has stopped sending it new requests; if the pod stops first, those requests fail.

</details>

Next: [13. Teardown and cost](13-teardown-and-cost.md)

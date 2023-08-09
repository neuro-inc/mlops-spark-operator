# Neuro Spark operator

Used to deploy [Spark operator](https://github.com/GoogleCloudPlatform/spark-on-k8s-operator) instance into the underlying k8s cluster.


## Quick start
Requires Helm v3+ to be installed and available in CLI.

- Install Spark operator.
```bash
platform-spark install spark-team --output kubeconfig
```
This will also generate kubectl config and dump it into specified in `--output` parameter path (cwd `kubeconfig` file).

This config could be used by end users to manage Spark Applications and pods within the specific namespace during installation ("spark-team" in this case).

- List installations
```bash
platform-spark list
```

- Deploy basic Spark app (on the user behalf, check output)
```bash
export KUBECONFIG=`pwd`/kubeconfig
kubectl apply -f tests/k8s/spark-app-pi.yaml
kubectl get sparkapplication
kubectl logs spark-pi-driver -f
```

Note, Spark app driver in [tests/k8s/spark-app-pi.yaml](tests/k8s/spark-app-pi.yaml) assumes the default service account name (spark-apps-editor), which might be customized.

- Remove Spark app and operator
```bash
kubectl delete -f tests/k8s/spark-app-pi.yaml
unset KUBECONFIG
platform-spark uninstall spark-team
rm kubeconfig
```

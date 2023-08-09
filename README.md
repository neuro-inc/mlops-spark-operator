# Neuro Spark operator

Used to deploy [Spark operator](https://github.com/GoogleCloudPlatform/spark-on-k8s-operator) instance into the underlying k8s cluster.


## Using Neuro Spark operator CLI
Requires Helm v3+ to be installed and available in CLI.

- Install Spark operator
```bash
platform-spark install spark-teamname --namespace spark-team
```

- List installations
```bash
platform-spark list [--namespace namespace]
```

- Generate kubectl config, which could be used to manage Spark Applications of Spark operator within the specific namespace.

```bash
platform-spark get-kubectl-config spark-team --output /path/to/cfg
```

- Deploy Spark app (on the user behalf)
```bash
export KUBECONFIG=/path/to/cfg
kubectl apply -f
```

- Remove operator
```bash
platform-spark uninstall spark-team
```


## Direct Helm:
Deploy using Helm directly:
```bash
helm install spark-teamname charts --namespace spark-team --create-namespace
```

Generate kubeconfig
```bash
%%bash
clusterName='my-cluster'
server=`kubectl cluster-info | sed 's/\x1B\[[0-9;]\{1,\}[A-Za-z]//g' | grep 'control plane' | awk '{print $NF}'`
namespace='spark-team'
serviceAccountName='spark'
secretName=$(kubectl --namespace="$namespace" get serviceAccount "$serviceAccountName" -o=jsonpath='{.secrets[0].name}')

ca=$(kubectl --namespace="$namespace" get secret/"$secretName" -o=jsonpath='{.data.ca\.crt}')
token=$(kubectl --namespace="$namespace" get secret/"$secretName" -o=jsonpath='{.data.token}' | base64 --decode)

echo "
---
apiVersion: v1
kind: Config
clusters:
  - name: ${clusterName}
    cluster:
      certificate-authority-data: ${ca}
      server: ${server}
contexts:
  - name: ${serviceAccountName}@${clusterName}
    context:
      cluster: ${clusterName}
      namespace: ${namespace}
      user: ${serviceAccountName}
users:
  - name: ${serviceAccountName}
    user:
      token: ${token}
current-context: ${serviceAccountName}@${clusterName}
" > sa_kubect.yaml
```

Now you could use the generated Kubeconfig to manage Spark apps and pods in the underlying namespace.

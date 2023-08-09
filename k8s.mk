K8S_CLUSTER_CMD := tests/k8s/cluster.sh

install_k8s:
	$(K8S_CLUSTER_CMD) install

start_k8s:
	$(K8S_CLUSTER_CMD) start

clean_k8s:
	$(K8S_CLUSTER_CMD) stop

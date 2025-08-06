## AutoMQ
### Background
AutoMQ is an innovative Apache Kafka alternative that features a pioneering decoupled compute and storage architecture. It leverages S3 object storage to reduce costs and optimize performance, among other benefits. This S3 storage includes cloud storage solutions like AWS S3, as well as on-premises object storage solutions such as MinIO.

In this case, I chose to deploy MinIO as the object storage solution to avoid the complexity associated with sharing external secrets.

### Links:
AWS Marketplace link: https://aws.amazon.com/marketplace/pp/prodview-suwr5pyxwakrk

Deploy on k8s overview: https://www.automq.com/docs/automq-cloud/deploy-automq-on-kubernetes/overview

Deploy to AWS EKS guide: https://www.automq.com/docs/automq-cloud/deploy-automq-on-kubernetes/deploy-to-aws-eks

### Testing
This is how I run the testjob locally.

Wait until all the pods are running:
```
vscode ➜ ~/conformitron (add-automq) $ kubectl get pods -n automq -w
NAME                             READY   STATUS              RESTARTS   AGE
minio-96cdf49fd-f4dnp            0/1     ContainerCreating   0          4s
minio-bucket-creator-5kvs8       0/1     ContainerCreating   0          10s
minio-console-5fdf78d6f5-vmkh9   0/1     ContainerCreating   0          4s
minio-bucket-creator-5kvs8       1/1     Running             0          21s
minio-96cdf49fd-f4dnp            0/1     Running             0          17s
minio-96cdf49fd-f4dnp            1/1     Running             0          23s
minio-bucket-creator-5kvs8       0/1     Completed           0          31s
minio-console-5fdf78d6f5-vmkh9   0/1     Running             0          25s
minio-bucket-creator-5kvs8       0/1     Completed           0          32s
minio-bucket-creator-5kvs8       0/1     Completed           0          33s
minio-console-5fdf78d6f5-vmkh9   1/1     Running             0          32s
automq-release-kafka-controller-0   0/1     Pending             0          0s
automq-release-kafka-controller-0   0/1     Pending             0          0s
automq-release-kafka-controller-0   0/1     Pending             0          0s
automq-release-kafka-controller-0   0/1     Init:0/1            0          0s
automq-release-kafka-controller-0   0/1     PodInitializing     0          10m
automq-release-kafka-controller-0   0/1     Running             0          10m
automq-release-kafka-controller-0   1/1     Running             0          10m
```
Manually creates the job:
```
Cvscode ➜ ~/conformitron (add-automq) kubectl create job manual-automq-test-1 --from=cronjob/automq-health-perf-test -n automqmq
job.batch/manual-automq-test-1 created
```
In this testjob, the script first creates a AutoMQ (Kafka) client. It then uses `kafka-broker-api-versions.sh` to test whether the kafka controller can be connected. If so, then uses `automq-perf-test.sh` to validate the functionality of AutoMQ. This script is for Kafka server throughout benchmark, the client node continuously produces messages to the server and consumes these messages at the same time. Therefore, I chose to run this script for one minute to show the AutoMQ pod works as expected. 
```
vscode ➜ ~/conformitron (add-automq) $ kubectl logs -f manual-automq-test-1-xfq42 -n automq
Starting AutoMQ health and performance test...
Testing Kafka connectivity directly...
Kafka connectivity test passed.
2025-08-06 14:08:21 - INFO Starting perf test with config: {
  "bootstrapServer" : "automq-release-kafka.automq.svc.cluster.local:9092",
  "commonConfigs" : { },
  "topicConfigs" : { },
  "producerConfigs" : {
    "batch.size" : "0"
  },
  "consumerConfigs" : {
    "fetch.max.wait.ms" : "1000"
  },
  "reset" : true,
  "topicPrefix" : "topic_1754489300951_8iRG",
  "topics" : 10,
  "partitionsPerTopic" : 12,
  "producersPerTopic" : 1,
  "groupsPerTopic" : 1,
  "consumersPerGroup" : 1,
  "awaitTopicReady" : true,
  "recordSize" : 200,
  "randomRatio" : 0.0,
  "randomPoolSize" : 1000,
  "sendRate" : 100,
  "sendRateDuringCatchup" : 100,
  "maxConsumeRecordRate" : 1000000000,
  "backlogDurationSeconds" : 0,
  "groupStartDelaySeconds" : 0,
  "warmupDurationMinutes" : 0,
  "testDurationMinutes" : 1,
  "reportingIntervalSeconds" : 1,
  "valueSchema" : null,
  "valuesFile" : null
}
2025-08-06 14:08:21 - INFO Deleting all test topics...
2025-08-06 14:08:21 - INFO Deleted all test topics (0 in total), took 255 ms
2025-08-06 14:08:21 - INFO Creating topics...
2025-08-06 14:08:21 - INFO Created 10 topics, took 107 ms
2025-08-06 14:08:21 - INFO Creating consumers...
2025-08-06 14:08:29 - INFO Created 10 consumers, took 7691 ms
2025-08-06 14:08:29 - INFO Creating producers...
2025-08-06 14:08:29 - INFO Created 10 producers, took 69 ms
2025-08-06 14:08:29 - INFO Waiting for topics to be ready...
2025-08-06 14:08:29 - INFO Waiting for topics to be ready... sent: 120, received: 0
2025-08-06 14:08:35 - INFO Waiting for topics to be ready... sent: 120, received: 120
2025-08-06 14:08:35 - INFO Topics are ready, took 5923 ms
2025-08-06 14:08:35 - INFO Running test for 1 minutes...
2025-08-06 14:08:36 - INFO    1.0s | Prod rate    107.78 msg/s /   0.02 MiB/s | Prod err      0.00 err/s | Cons rate    107.78 msg/s /   0.02 MiB/s | Backlog:   0.00 K msg | Prod Latency (ms) avg:   161.608 - 50%:   163.310 - 99%:   293.071 - 99.9%:   293.405 - Max:   293.405 | E2E Latency (ms) avg:   166.103 - 50%:   166.410 - 99%:   299.355 - 99.9%:   300.623 - Max:   300.623
2025-08-06 14:08:37 - INFO    2.2s | Prod rate     90.19 msg/s /   0.02 MiB/s | Prod err      0.00 err/s | Cons rate     90.19 msg/s /   0.02 MiB/s | Backlog:   0.00 K msg | Prod Latency (ms) avg:   153.501 - 50%:   149.191 - 99%:   278.603 - 99.9%:   279.137 - Max:   279.137 | E2E Latency (ms) avg:   157.727 - 50%:   158.988 - 99%:   284.819 - 99.9%:   285.533 - Max:   285.533
2025-08-06 14:08:38 - INFO    3.3s | Prod rate     90.78 msg/s /   0.02 MiB/s | Prod err      0.00 err/s | Cons rate    113.47 msg/s /   0.02 MiB/s | Backlog:   0.00 K msg | Prod Latency (ms) avg:   156.086 - 50%:   154.863 - 99%:   281.075 - 99.9%:   283.769 - Max:   283.769 | E2E Latency (ms) avg:   158.514 - 50%:   157.063 - 99%:   280.005 - 99.9%:   298.027 - Max:   298.027
2025-08-06 14:08:40 - INFO    4.4s | Prod rate    115.85 msg/s /   0.02 MiB/s | Prod err      0.00 err/s | Cons rate     92.68 msg/s /   0.02 MiB/s | Backlog:   0.00 K msg | Prod Latency (ms) avg:   159.309 - 50%:   157.371 - 99%:   296.303 - 99.9%:   301.051 - Max:   301.051 | E2E Latency (ms) avg:   162.223 - 50%:   165.158 - 99%:   294.667 - 99.9%:   299.533 - Max:   299.533
2025-08-06 14:08:41 - INFO    5.6s | Prod rate     98.28 msg/s /   0.02 MiB/s | Prod err      0.00 err/s | Cons rate    120.69 msg/s /   0.02 MiB/s | Backlog:   0.00 K msg | Prod Latency (ms) avg:   157.317 - 50%:   162.999 - 99%:   285.357 - 99.9%:   286.497 - Max:   286.497 | E2E Latency (ms) avg:   159.075 - 50%:   165.311 - 99%:   287.233 - 99.9%:   287.545 - Max:   287.545
2025-08-06 14:08:42 - INFO    6.7s | Prod rate    116.71 msg/s /   0.02 MiB/s | Prod err      0.00 err/s | Cons rate     93.37 msg/s /   0.02 MiB/s | Backlog:   0.00 K msg | Prod Latency (ms) avg:   154.586 - 50%:   154.745 - 99%:   278.817 - 99.9%:   281.861 - Max:   281.861 | E2E Latency (ms) avg:   156.278 - 50%:   156.104 - 99%:   281.733 - 99.9%:   282.235 - Max:   282.235
```
Skip some logs...
```
2025-08-06 14:09:35 - INFO   59.9s | Prod rate     89.10 msg/s /   0.02 MiB/s | Prod err      0.00 err/s | Cons rate     89.10 msg/s /   0.02 MiB/s | Backlog:   0.00 K msg | Prod Latency (ms) avg:   145.224 - 50%:   146.075 - 99%:   271.145 - 99.9%:   275.081 - Max:   275.081 | E2E Latency (ms) avg:   145.912 - 50%:   144.236 - 99%:   273.049 - 99.9%:   273.867 - Max:   273.867
2025-08-06 14:09:36 - INFO   61.0s | Prod rate     99.29 msg/s /   0.02 MiB/s | Prod err      0.00 err/s | Cons rate    121.25 msg/s /   0.02 MiB/s | Backlog:   0.00 K msg | Prod Latency (ms) avg:   147.152 - 50%:   147.281 - 99%:   269.851 - 99.9%:   281.647 - Max:   281.647 | E2E Latency (ms) avg:   148.657 - 50%:   148.552 - 99%:   276.129 - 99.9%:   281.263 - Max:   281.263
2025-08-06 14:09:36 - INFO Summary | Prod rate    101.90 msg/s /   0.02 MiB/s | Prod total   0.01 M msg /   0.00 GiB /   0.00 K err | Cons rate    101.90 msg/s /   0.02 MiB/s | Cons total   0.01 M msg /   0.00 GiB | Prod Latency (ms) avg:   156.428 - 50%:   155.307 - 75%:   219.818 - 90%:   258.474 - 95%:   271.859 - 99%:   335.155 - 99.9%:   510.029 - 99.99%:   543.787 - Max:   543.787 | E2E Latency (ms) avg:   158.226 - 50%:   157.286 - 75%:   221.835 - 90%:   260.425 - 95%:   274.539 - 99%:   340.693 - 99.9%:   518.985 - 99.99%:   552.215 - Max:   552.215
2025-08-06 14:09:36 - INFO Saving results to perf-2025-08-06-14-09-36.json
Success: Performance test completed without errors.
```
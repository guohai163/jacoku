## jaocoo报告抓取

本项目需要工作在K8s环境内，通过jacoco agent项目来dump java项目的测试覆盖率。并通过pod上的git commit值来下载对应的代码生成覆盖率报告。
最终报告会上传到minio的对象存储中。
通过以上方案可以节省开发人员书写单元测试，并可以观测自动/功能的测试覆盖业务情况。

![frame-diagram](./images/frame-diagram.svg)



## 相关资料

* [Kubernetes](https://kubernetes.io/)
* [Java Code Coverage](https://www.jacoco.org/)
* [MinIO](https://min.io/)
* [Sonar](https://www.sonarsource.com/)
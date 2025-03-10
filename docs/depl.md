## 环境准备

本程序需要运行在kubernetes 1.24以上版本，同时K8s内需要安装有ingress支持。同时为了快速部署需要安装[helm支持](https://helm.sh/)。

## 本项目部署方法

快速启动脚本，需要按你的实际环境修改 ingress域名和ingress驱动类。

~~~ shell
kubectl create ns jacoku
helm repo add jacoku https://guohai163.github.io/jacoku
helm repo update
helm upgrade --install jacoku-report -n jacoku jacoku/jacoku \
    --set 'ingress.enabled=true' \
    --set 'ingress.className=nginx' \
    --set 'ingress.host=demo.jacoku.cn'
~~~
   
正常启动后，可以打开浏览器访问 http://demo.jacoku.cn 查看安装情况。正常情况下是没有能够支持覆盖率的POD容器的，我们来创建一个测试体

~~~ shell
kubectl apply -f https://guohai163.github.io/jacoku-testee/k8s-pod.yaml
~~~

重新打开 jacoku容器监控页面，可以看来新建立的测试POD，点击 生成报告 会开始进行分析。


![type:video](./videos/jacoku-guid-1.mp4)
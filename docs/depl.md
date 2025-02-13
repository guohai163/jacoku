## 本项目部署方法

推荐使用helm来启动本项目。需要准备好 minio的环境,新建一个名为jacoco-report的存储桶并生成好对应 的key。同时本项目会在K8s集群内创建一个服务账号用来请求集群内的注解权限。

~~~ shell
 kubectl create ns jacoco-report
 helm repo add jacoco-report https://guohai163.github.io/jacoco-report 
 helm repo update
 helm upgrade --install jacoco-report jacoco-report/jacoco-report \
     --set 'extraEnvs[0].name=MINIO_URL,extraEnvs[0].value=minio.xxx.x' \
     --set 'extraEnvs[1].name=MINIO_ACCESS,extraEnvs[1].value=xxx' \
     --set 'extraEnvs[2].name=MINIO_SECRET,extraEnvs[2].value=xxx'
~~~
   
正常启动后，项目会在每日凌晨1点对k8s内项目进行扫描并生成结果到存储桶内。
'use client';
import {useEffect, useState} from "react";
import { Table, Button, Switch } from 'antd';
import type { TableProps } from 'antd';


interface DataType {
    pod_ns: string;
    pod_name: string;
    enable: boolean;
    git_commit: string;
    git_url: string;
    src_path: string;
}

export default function Home() {
  const [data, setData] = useState();
  useEffect(()=>{

    fetch('/api/list')
        .then(response => response.json())
        .then(data => {
          console.log(data)
          setData(data)
        })
        .catch(error => console.error(error))
  },[]);
  const codeCoverage = async (podParam:DataType) =>{
      console.log('function codeCoverage'+podParam.pod_ns)
      await fetch('/api/analysis', {
          body: JSON.stringify(podParam),
          method: "POST"
      })
          .then(response => response.json())
          .then(data=> console.log(data))
  }

  const colorLogPrint = (color: string, message: string) =>{
      const cssMap = new Map();
      cssMap.set('green','color:#42c731;background-color:#1E1E1E;padding:3px;');
      cssMap.set('cyan','color:#41c5d1;background-color:#1E1E1E;padding:3px;');
      cssMap.set('white','color:#ffffff;background-color:#1E1E1E;padding:3px;');
      cssMap.set('orange','color:#d64a2e;background-color:#1E1E1E;padding:3px;');
      console.log("%c%s",cssMap.get(color),message)
  }

    const columns: TableProps<DataType>['columns'] = [
        { key: 'pod_ns', title: 'pod namespace', dataIndex: 'pod_ns'},
        { key: 'pod_name', title: 'pod name', dataIndex: 'pod_name' },
        { key: 'enable', title: '是否开启jacoco注解', dataIndex: 'enable',
            filters:[{ text: 'True', value: true }, { text: 'False', value: false}],
            onFilter: (value, record) => record.enable === value,
            render: (text: boolean) => <>{text?<Switch disabled={true} checkedChildren="开启" unCheckedChildren="关闭" defaultChecked />:<></>}</>},
        { key: 'src_path', title: '路径', dataIndex: 'src_path' },
        { key: 'git_commit', title: 'git', dataIndex: 'git_commit',
            render: (_, record: DataType) =>(
                <a href={record.git_url.replace(/.git$/g,"")+'/-/tree/'+record.git_commit} target={'_blank'}>{record.git_commit}</a>
            )},
        { key: 'last_check_time', title: '最后检查时间', dataIndex: 'last_check_time' },
        { key: 'html_link', title: 'HTML报告', dataIndex: 'html_link', render: (text: string) => (
            <>
                {text != null && text.length>0?<a href={text} target={'_blank'}>查看报告</a>:<></>}
            </>
            )
        },
        { key: 'action', title:'生成报告', render: (_, record: DataType)=>(
            <>
                {record.enable?<Button type={"primary"} onClick={() => {
                    const ws:WebSocket = new WebSocket("/api/ws")
                    ws.onopen = function (){
                        colorLogPrint("green","🐠🪸🦞🐡准备开始分析代码🐡🦞🪸🐠")
                        ws.send( JSON.stringify(record))

                    }
                    ws.onmessage = function (evt){
                        colorLogPrint(evt.data.returnCode<=0?"white":"orange",evt.data.message)
                    }
                    ws.onclose = function (){
                        colorLogPrint("cyan","🐠🪸🦞🐡代码分析结束🐡🦞🪸🐠")
                        alert('执行结束')
                    }
                }}>生成报告</Button>:<></>}
            </>

            )}
        ];
  return (
      <div>
          <Table<DataType> dataSource={data} columns={columns} />
      </div>
  );
}

'use client';
import {useEffect, useState} from "react";
import { Space, Table, Tag, Button } from 'antd';
import type { TableProps } from 'antd';

interface DataType {
    pod_ns: string;
    pod_name: string;
    enable: boolean;
}

export default function Home() {
  const [data, setData] = useState();
  useEffect(()=>{

    fetch('http://jacoku.cn/api/list')
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

    const columns: TableProps<DataType>['columns'] = [
        { key: 'pod_ns', title: 'pod namespace', dataIndex: 'pod_ns'},
        { key: 'pod_name', title: 'pod name', dataIndex: 'pod_name' },
        { key: 'enable', title: '是否开启jacoco注解', dataIndex: 'enable',
            filters:[{ text: 'True', value: 'True'}, { text: 'False', value: 'False'}]},
        { key: 'git_url', title: 'git', dataIndex: 'git_url' },
        { key: 'git_commit', title: 'git commit', dataIndex: 'git_commit' },
        { key: 'last_check_time', title: '最后检查时间', dataIndex: 'last_check_time' },
        { key: 'html_link', title: 'HTML报告', dataIndex: 'html_link', render: (text: string) => (
            <>
                {text != null && text.length>0?<a href={text} target={'_blank'}>查看报告</a>:<></>}
            </>
            )
        },
        { key: 'action', title:'生成报告', render: (_: any, record: DataType)=>(
            <>
                {record.enable?<Button type="primary" onClick={() => codeCoverage(record)}>生成报告</Button>:<></>}
            </>

            )}
        ];
  return (
      <div>
          <Table<DataType> dataSource={data} columns={columns} />
      </div>
  );
}

'use client';
import '@ant-design/v5-patch-for-react-19';
import {ReactNode, useEffect, useState} from "react";
import { Table, Button, Switch, Alert, message, Modal, Timeline } from 'antd';
import type { TableProps } from 'antd';


interface DataType {
    pod_ns: string;
    pod_name: string;
    enable: boolean;
    git_commit: string;
    git_url: string;
    src_path: string;
}

interface ITimeLine {
    children: string;
    color: string;
}

export default function Home() {
  const [data, setData] = useState();
  const [messageApi] = message.useMessage();
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  // 关闭按钮是否显示
  const [modalCloseButton, setModalCloseButton] = useState(false);
  const [processTime, setProcessTime] = useState<ITimeLine[]>([]);
  const [pendingTime,setPendingTime] = useState<ReactNode>();
  const [lastData, setLastData] = useState<ITimeLine>();
  useEffect(()=>{
      setLoading(true);
      fetch('//jacoku.cn/api/list')
        .then(response => response.json())
        .then(data => {
          setData(data);
          setLoading(false);
        })
        .catch(error => console.error(error))
  },[]);

  const timeAdd = (message: string, icon: string) => {

      if(icon=="green"){
          // 正常开始
          setLastData({children: message, color: icon})
          setPendingTime(message)
          return
      }
      if(icon=="red" ){
          // 上一步出错
          const pro = processTime;
          pro.push( {children: (lastData as ITimeLine).children, color: "red"})
          setProcessTime(pro)
          setPendingTime(false)
          return;
      }
      if(icon=="cyan"){
          // 结束了
          const pro = processTime;
          pro.push(lastData as ITimeLine)
          pro.push( {children: message, color: icon})
          setProcessTime(pro)
          setPendingTime(false)
          return;
      }
      // 正常过程中

      const pro = processTime;
      pro.push(lastData as ITimeLine)
      setProcessTime(pro)
      setLastData({children: message, color: icon})
      setPendingTime(message);


  }

  const colorLogPrint = (color: string, message: string) =>{
      const cssMap = new Map();
      cssMap.set('green','color:#42c731;background-color:#1E1E1E;padding:3px;');
      cssMap.set('cyan','color:#41c5d1;background-color:#1E1E1E;padding:3px;');
      cssMap.set('white','color:#ffffff;background-color:#1E1E1E;padding:3px;');
      cssMap.set('orange','color:#d64a2e;background-color:#1E1E1E;padding:3px;');
      console.log("%c%s",cssMap.get(color),message);
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
                    const ws:WebSocket = new WebSocket("//jacoku.cn/api/ws")
                    ws.onopen = function (){
                        colorLogPrint("green","🐠🐟🦞🐡准备开始分析代码🐡🦞🐟🐠")

                        ws.send( JSON.stringify(record))
                        setIsModalOpen(true)
                        timeAdd("🐠🐟🦞🐡准备开始分析代码🐡🦞🐟🐠", "green")

                    }
                    ws.onmessage = function (evt){
                        const wsMessage = JSON.parse(evt.data)
                        colorLogPrint(wsMessage.returnCode==0?"white":"orange",wsMessage.message)
                        if(wsMessage.process != "") {
                            timeAdd(wsMessage.process + " " + wsMessage.message, "blue");
                        }
                        if(wsMessage.returnCode>0){
                            timeAdd("","red");

                        }

                    }
                    ws.onclose = function (){
                        colorLogPrint("cyan","🎄🌲🌳🌴代码分析结束🌴🌳🌲🎄")
                        timeAdd("🎄🌲🌳🌴代码分析结束🌴🌳🌲🎄", "cyan")
                        setModalCloseButton(true);
                    }
                }}>生成报告</Button>:<></>}
            </>

            )}
        ];
  return (
      <div>
          <Alert message="POD需要增加注解，才可被程序自动发现" type="warning" showIcon closable />
          <Table<DataType> dataSource={data} columns={columns} loading={loading} rowKey={record=>record.pod_name}/>
          <Modal title={"处理过程"} open={isModalOpen} closable={modalCloseButton} footer={null}
            onClose={()=>setIsModalOpen(false)}>
              <Timeline
                  pending={pendingTime}
                  items={processTime}

              ></Timeline>
          </Modal>
      </div>
  );
}
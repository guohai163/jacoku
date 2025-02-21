'use client';
import '@ant-design/v5-patch-for-react-19';
import {ReactNode, useEffect, useState} from "react";
import { Table, Button, Switch, Alert, message, Modal, Timeline, Spin } from 'antd';
import type { TableProps } from 'antd';
import {LoadingOutlined} from "@ant-design/icons";


interface DataType {
    pod_ns: string;
    pod_name: string;
    enable: boolean;
    git_commit: string;
    git_url: string;
    src_path: string;
    build_path_switch: boolean;
}

interface ITimeLine {
    children: string;
    color: string;
    dot?: ReactNode;
}

export default function Home() {
  const [jacokuData, setJacokuData] = useState<DataType[]>([]);
  const [messageApi] = message.useMessage();
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  // 关闭按钮是否显示
  const [modalCloseButton, setModalCloseButton] = useState(false);
  const [processTime, setProcessTime] = useState<ITimeLine[]>([]);
  const [pendingTime,setPendingTime] = useState<ReactNode>();
  const [lastData, setLastData] = useState<ITimeLine>();
  const [wsData, setWsData] = useState<{ pending: ReactNode | false, items: ITimeLine[] }>();

  useEffect(()=>{
      setLoading(true);
      fetch('//jacoku.cn/api/list')
        .then(response => response.json())
        .then(data => {
          setJacokuData(data);
          setLoading(false);
        })
        .catch(error => console.error(error))
  },[]);

  const handleWsData = (message: string, icon: string) => {

      if(icon=="green"){
          // 正常开始
          setLastData({children: message, color: icon})
          setPendingTime(message)
          return {children: message, color: icon};
      }
      if(icon=="red" ){
          // 上一步出错
          const pro = processTime;
          pro.push( {children: (lastData as ITimeLine).children, color: "red"})
          setProcessTime(pro)
          setPendingTime(false)
          return {children: message, color: icon};
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
      { key: 'build_path_switch', title: '构建路径', dataIndex: 'build_path_switch', render: (val:boolean, record: DataType) => (
          <>
            <Switch onChange={(checked)=>{
                let data: DataType[] = jacokuData
                data.forEach((item) => {
                    if (item.pod_name == record.pod_name){
                        item.build_path_switch = checked
                    }
                })
                setJacokuData(data)
            }}></Switch>
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
                        setWsData({
                            pending: false,
                            items: [{children: '🐠🐟🦞🐡准备开始分析代码🐡🦞🐟🐠', color: 'green'}],
                        });

                    }
                    ws.onmessage = function (evt){
                        const wsMessage = JSON.parse(evt.data)
                        colorLogPrint(wsMessage.returnCode==0?"white":"orange",wsMessage.returnCode+"_"+wsMessage.message)

                        // 更新 wsData 状态
                        setWsData(prevData => {
                            const updatedItems = prevData?.items ? [...prevData.items] : [];

                            // 更新其他条目的 dot 属性为空

                            if(wsMessage.process!="") {
                                // 根据返回的数据，处理 timeline 的条目
                                updatedItems.push({
                                    dot: <Spin indicator={<LoadingOutlined spin/>}/>,
                                    children: `${wsMessage.process} ${wsMessage.message}`,
                                    color: "blue"
                                });
                            }else{
                                if(wsMessage.returnCode>0) {
                                    updatedItems.forEach((item, index) => {
                                        if (index == updatedItems.length-1) {
                                            item.color = "red";  // 出错，最后一条标红
                                            item.dot = undefined;  // 删除除最后一项外其他条目的 dot 属性
                                        }
                                    });
                                }else {
                                    updatedItems.forEach((item, index) => {
                                        if (index < updatedItems.length ) {
                                            item.dot = undefined;  // 删除除最后一项外其他条目的 dot 属性
                                        }
                                    });
                                }
                            }



                            return {
                                pending: wsMessage.returnCode <= 0 ? `${wsMessage.process} ${wsMessage.message}` : false,
                                items: updatedItems
                            };
                        });


                    }
                    ws.onclose = function (){
                        colorLogPrint("cyan","🎄🌲🌳🌴代码分析结束🌴🌳🌲🎄")
                        setWsData(prevData => {
                            const updatedItems = prevData?.items ? [...prevData.items] : [];

                            updatedItems.forEach((item) => {
                                delete item.dot;
                            });
                            // 根据返回的数据，处理 timeline 的条目
                            updatedItems.push({
                                children: `🎄🌲🌳🌴代码分析结束🌴🌳🌲🎄`,
                                color: 'cyan',
                            });
                            return {
                                pending: false,
                                items: updatedItems
                            };
                        });
                        setModalCloseButton(true);
                    }
                }}>生成报告</Button>:<></>}
            </>

            )}
        ];
  return (
      <div>
          <Alert message="POD需要增加注解，才可被程序自动发现" type="warning" showIcon closable />
          <Table<DataType> dataSource={jacokuData} columns={columns} loading={loading} rowKey={record=>record.pod_name}/>
          <Modal title={"处理过程"} open={isModalOpen} closable={modalCloseButton} footer={null}
                 onCancel={()=>setIsModalOpen(false)}>
              <Timeline
                  items={wsData?.items ?? []}

              ></Timeline>
          </Modal>
      </div>
  );
}
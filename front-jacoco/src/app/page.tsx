'use client';
import {ReactNode, useEffect, useState, useRef} from "react";
import {Table, Button, Switch, Alert, Modal, Timeline, Spin, Input, Space} from 'antd';
import type { TableProps, InputRef, TableColumnType } from 'antd';
import {CheckCircleTwoTone, LoadingOutlined, WarningTwoTone, SearchOutlined} from "@ant-design/icons";
import type { FilterDropdownProps } from 'antd/es/table/interface';
import Highlighter from 'react-highlight-words';

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

type DataIndex = keyof DataType;
export default function Home() {
  const [jacokuData, setJacokuData] = useState<DataType[]>([]);
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  // 关闭按钮是否显示
  const [modalCloseButton, setModalCloseButton] = useState(false);
  const [wsData, setWsData] = useState<{ pending: ReactNode | false, items: ITimeLine[] }>();
  const searchInput = useRef<InputRef>(null);
  const [searchText, setSearchText] = useState('');
  const [searchedColumn, setSearchedColumn] = useState('');


  useEffect(()=>{
      setLoading(true);
      fetch('/api/list')
        .then(response => response.json())
        .then(data => {
          setJacokuData(data);
          setLoading(false);
        })
        .catch(error => console.error(error))
  },[]);


  const colorLogPrint = (color: string, message: string) =>{
      const cssMap = new Map();
      cssMap.set('green','color:#42c731;background-color:#1E1E1E;padding:3px;');
      cssMap.set('cyan','color:#41c5d1;background-color:#1E1E1E;padding:3px;');
      cssMap.set('white','color:#ffffff;background-color:#1E1E1E;padding:3px;');
      cssMap.set('orange','color:#d64a2e;background-color:#1E1E1E;padding:3px;');
      console.log("%c%s",cssMap.get(color),message);
  }
    const handleSearch = (
        selectedKeys: string[],
        confirm: FilterDropdownProps['confirm'],
        dataIndex: DataIndex,
    ) => {
      console.log(selectedKeys)
        confirm();
        setSearchText(selectedKeys[0]);
        setSearchedColumn(dataIndex);
    };
    const handleReset = (clearFilters: () => void) => {
        clearFilters();
        setSearchText('');
    };
    const getColumnSearchProps = (dataIndex: DataIndex):TableColumnType<DataType> => ({
        filterDropdown: ({setSelectedKeys, selectedKeys, confirm, clearFilters, close}) => (
            <div style={{ padding: 8 }} onKeyDown={(e) => e.stopPropagation()}>
                <Input
                    ref={searchInput}
                    placeholder={`Search ${dataIndex}`}
                    value={selectedKeys[0]}
                    onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
                    onPressEnter={() => handleSearch(selectedKeys as string[], confirm, dataIndex)}
                    style={{ marginBottom: 8, display: 'block' }}
                />
                <Space>
                    <Button
                        type="primary"
                        onClick={() => handleSearch(selectedKeys as string[], confirm, dataIndex)}
                        icon={<SearchOutlined />}
                        size="small"
                        style={{ width: 90 }}
                    >
                        Search
                    </Button>
                    <Button
                        onClick={() => clearFilters && handleReset(clearFilters)}
                        size="small"
                        style={{ width: 90 }}
                    >
                        Reset
                    </Button>
                    <Button
                        type="link"
                        size="small"
                        onClick={() => {
                            confirm({ closeDropdown: false });
                            setSearchText((selectedKeys as string[])[0]);
                            setSearchedColumn(dataIndex);
                        }}
                    >
                        Filter
                    </Button>
                    <Button
                        type="link"
                        size="small"
                        onClick={() => {
                            close();
                        }}
                    >
                        close
                    </Button>
                </Space>
            </div>
        ),
        filterIcon: (filtered: boolean) => (
            <SearchOutlined style={{ color: filtered ? '#1677ff' : undefined }} />
        ),
        onFilter: (value, record) =>
            record[dataIndex]
                .toString()
                .toLowerCase()
                .includes((value as string).toLowerCase()),
        filterDropdownProps: {
            onOpenChange(open) {
                if (open) {
                    setTimeout(() => searchInput.current?.select(), 100);
                }
            },
        },
        render: (text) =>
            searchedColumn === dataIndex ? (
                <Highlighter
                    highlightStyle={{ backgroundColor: '#ffc069', padding: 0 }}
                    searchWords={[searchText]}
                    autoEscape
                    textToHighlight={text ? text.toString() : ''}
                />
            ) : (
                text
            ),
    })

    const columns: TableProps<DataType>['columns'] = [
        { key: 'pod_ns', title: 'pod namespace', dataIndex: 'pod_ns'},
        { key: 'pod_name', title: 'pod name', dataIndex: 'pod_name',
            ...getColumnSearchProps('pod_name')},
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
                {(text != null && text.length>0)?<a href={text} target={'_blank'}>查看报告</a>:<></>}
            </>
            )
      },
      { key: 'build_path_switch', title: '构建路径', dataIndex: 'build_path_switch', render: (val:boolean, record: DataType) => (
          <>
            <Switch defaultValue={val} onChange={(checked)=>{

                record.build_path_switch = checked

            }}></Switch>
          </>
          )

      },
        { key: 'action', title:'生成报告', render: (_, record: DataType)=>(
            <>
                {record.enable?<Button type={"primary"} onClick={() => {
                    const ws:WebSocket = new WebSocket("/api/ws")
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
                        colorLogPrint(wsMessage.returnCode==0?"white":"orange",wsMessage.message)

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
                            let buildSuccess:boolean = true
                            updatedItems.forEach((item) => {
                                delete item.dot;
                                if(item.color=="red"){

                                    buildSuccess = false;
                                }
                            });

                            // 根据返回的数据，处理 timeline 的条目
                            updatedItems.push({
                                color: "blue",
                                children: buildSuccess?`🎄🌲🌳🌴代码分析结束🌴🌳🌲🎄`:`🎄🌲🌳🌴请打开控制台查看详细错误🎄🌲🌳🌴`,
                                dot: buildSuccess?<CheckCircleTwoTone twoToneColor="#52c41a"/>:<WarningTwoTone twoToneColor="#eb2f96" />
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
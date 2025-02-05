'use client';
import {useEffect, useState} from "react";
import { DataGrid, GridColDef } from '@mui/x-data-grid';

import Box from '@mui/material/Box';

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
    const columns: GridColDef<(typeof data)[number]>[] = [
        { field: 'pod_ns', headerName: 'pod namespace', width: 100 },
        { field: 'pod_name', headerName: 'pod name', width: 150 },
        { field: 'enable', headerName: '是否开启jacoco注解', width: 140 },
        { field: 'git_url', headerName: 'git', width: 300 },
        { field: 'git_commit', headerName: 'git commit', width: 200 },
        { field: 'last_check_time', headerName: '最后检查时间', width: 140 },
        ];
  return (
      <Box sx={{ height: '100%', width: '100%' }}>
      <DataGrid
          columns={columns}
          rows={data}
          getRowId={(row) =>  row.pod_name}
          initialState={{
              pagination: {
                  paginationModel: {
                      pageSize: 50,
                  },
              },
          }}
          pageSizeOptions={[50]}

      ></DataGrid>
        </Box>
  );
}

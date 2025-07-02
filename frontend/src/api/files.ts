import api from '@/utils/api'

export interface FileInfo {
  name: string
  path: string
  size: number
  modified: string
  is_main: boolean
}

export interface FileListResponse {
  files: FileInfo[]
  main_file?: string
}

// 获取文件列表
export const getFileList = () => {
  return api.get('/files/')
}

// 获取文件内容
export const getFileContent = (filename: string) => {
  return api.get(`/files/${filename}/content`)
}

// 更新文件内容
export const updateFileContent = (filename: string, content: string) => {
  return api.put(`/files/${filename}/content`, { content })
}

// 上传文件
export const uploadFile = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/files/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 删除文件
export const deleteFile = (filename: string) => {
  return api.delete(`/files/${filename}`)
}

// 验证文件
export const validateFile = (filename: string) => {
  return api.post(`/files/${filename}/validate`)
} 
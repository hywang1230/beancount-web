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

export interface FileTreeNode {
  name: string
  path: string
  size: number
  type: string
  is_main: boolean
  includes: FileTreeNode[]
  modified?: number
  error?: string
}

export interface FileTreeResponse {
  tree: FileTreeNode
  total_files: number
  main_file: string
}

// 获取文件列表
export const getFileList = () => {
  return api.get('/files/')
}

// 获取文件树结构
export const getFileTree = () => {
  return api.get('/files/tree')
}

// 获取文件内容（支持相对路径）
export const getFileContent = (filePath: string) => {
  return api.get('/files/content', { params: { file_path: filePath } })
}

// 获取文件内容（兼容旧接口）
export const getFileContentLegacy = (filename: string) => {
  return api.get(`/files/${filename}/content`)
}

// 更新文件内容（支持相对路径）
export const updateFileContent = (filePath: string, content: string) => {
  return api.put('/files/content', { content }, { params: { file_path: filePath } })
}

// 更新文件内容（兼容旧接口）
export const updateFileContentLegacy = (filename: string, content: string) => {
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
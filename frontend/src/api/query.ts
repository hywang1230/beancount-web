import api from "@/utils/api";

export interface BQLQueryRequest {
  query: string;
}

export interface BQLQueryResponse {
  success: boolean;
  columns: string[];
  rows: any[][];
  types: string[];
  row_count: number;
  error?: string;
}

export interface BQLQueryExample {
  name: string;
  description: string;
  query: string;
}

export interface BQLFunction {
  name: string;
  description: string;
  example: string;
}

export interface SavedQuery {
  id?: number;
  name: string;
  description?: string;
  query: string;
  created_at?: string;
  updated_at?: string;
}

// 执行 BQL 查询
export const executeQuery = (data: BQLQueryRequest): Promise<BQLQueryResponse> => {
  return api.post("/query/execute", data);
};

// 验证 BQL 查询语法
export const validateQuery = (data: BQLQueryRequest): Promise<{ valid: boolean; error?: string }> => {
  return api.post("/query/validate", data);
};

// 获取查询示例
export const getQueryExamples = (): Promise<BQLQueryExample[]> => {
  return api.get("/query/examples");
};

// 获取可用函数列表
export const getAvailableFunctions = (): Promise<BQLFunction[]> => {
  return api.get("/query/functions");
};

// 获取保存的查询列表
export const getSavedQueries = (): Promise<SavedQuery[]> => {
  return api.get("/query/saved");
};

// 保存查询
export const saveQuery = (data: SavedQuery): Promise<SavedQuery> => {
  return api.post("/query/saved", data);
};

// 获取特定的保存查询
export const getSavedQuery = (id: number): Promise<SavedQuery> => {
  return api.get(`/query/saved/${id}`);
};

// 更新保存的查询
export const updateSavedQuery = (id: number, data: SavedQuery): Promise<SavedQuery> => {
  return api.put(`/query/saved/${id}`, data);
};

// 删除保存的查询
export const deleteSavedQuery = (id: number): Promise<{ success: boolean; message: string }> => {
  return api.delete(`/query/saved/${id}`);
};


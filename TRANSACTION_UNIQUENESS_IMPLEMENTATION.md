# 交易记录唯一性改进实现

## 概述

本次改进实现了基于文件名+行号的交易记录唯一性标识，参考了 Fava 的实现方式。这种方式比简单的递增ID更加稳定和可靠，特别适合 Beancount 这种基于文本文件的记账系统。

## 实现方案

### 1. 数据模型改进

#### 后端数据模型 (`backend/app/models/schemas.py`)
```python
class TransactionResponse(TransactionBase):
    postings: List[PostingBase]
    # 添加唯一标识字段
    filename: Optional[str] = None          # 交易所在文件的完整路径
    lineno: Optional[int] = None            # 交易在文件中的行号
    transaction_id: Optional[str] = None    # 由filename+lineno组成的唯一标识
```

#### 前端数据模型 (`frontend/src/api/transactions.ts`)
```typescript
export interface Transaction {
  date: string
  flag: string
  payee?: string
  narration: string
  tags?: string[]
  links?: string[]
  postings: Posting[]
  // 添加唯一标识字段
  filename?: string         // 交易所在文件名
  lineno?: number          // 交易在文件中的行号
  transaction_id?: string  // 由filename+lineno组成的唯一标识
}
```

### 2. 元数据提取

#### Beancount 元数据提取 (`backend/app/services/beancount_service.py`)
Beancount 在解析文件时会自动为每个 Entry 添加元数据：
- `filename`: 交易记录所在的文件名
- `lineno`: 交易记录在文件中的行号

我们的实现提取这些元数据并生成唯一标识：
```python
# 提取文件名和行号元数据
filename = entry.meta.get('filename') if entry.meta else None
lineno = entry.meta.get('lineno') if entry.meta else None

# 生成唯一的交易ID
transaction_id = None
if filename and lineno:
    relative_filename = os.path.basename(filename)
    transaction_id = f"{relative_filename}:{lineno}"
```

### 3. API 接口改进

#### 新增的 RESTful 接口
- `GET /api/transactions/{transaction_id}` - 根据唯一标识获取单个交易
- `PUT /api/transactions/{transaction_id}` - 根据唯一标识更新交易
- `DELETE /api/transactions/{transaction_id}` - 根据唯一标识删除交易

其中 `transaction_id` 的格式为 `filename:lineno`，例如：`main.beancount:972`

#### 前端 API 调用
```typescript
// 根据transaction_id获取单个交易
export const getTransactionById = (transactionId: string) => {
  return api.get(`/transactions/${transactionId}`)
}

// 根据transaction_id更新交易
export const updateTransaction = (transactionId: string, data: Transaction) => {
  return api.put(`/transactions/${transactionId}`, data)
}

// 根据transaction_id删除交易
export const deleteTransaction = (transactionId: string) => {
  return api.delete(`/transactions/${transactionId}`)
}
```

### 4. 前端页面改进

#### PC端交易页面 (`frontend/src/views/pc/Transactions.vue`)
```typescript
// 使用文件名+行号作为唯一标识
const transactionId = transaction.transaction_id || `transaction-${transactionIndex}`

result.push({
  id: transactionId,
  transactionId: transaction.transaction_id,
  filename: transaction.filename,
  lineno: transaction.lineno,
  // ... 其他字段
})
```

#### H5端交易页面 (`frontend/src/views/h5/Transactions.vue`)
```typescript
return {
  id: trans.transaction_id || `transaction-${transactions.value.length + index + 1}`,
  transaction_id: trans.transaction_id,
  filename: trans.filename,
  lineno: trans.lineno,
  // ... 其他字段
}
```

## 优势

### 1. 稳定性
- 基于文件位置的唯一标识比递增ID更稳定
- 交易在文件中的位置是固定的，不会因为数据加载顺序而改变

### 2. 可追溯性
- 可以直接定位到交易在原始文件中的具体位置
- 便于调试和数据验证

### 3. 兼容性
- 与 Fava 的实现方式兼容
- 利用了 Beancount 原生的元数据机制

### 4. 扩展性
- 支持多文件的 Beancount 项目
- 每个文件中的交易都有独立的唯一标识

## 使用示例

### API 调用示例
```bash
# 获取所有交易（包含唯一标识）
curl "http://localhost:8000/api/transactions/?page=1&page_size=5"

# 根据唯一标识获取单个交易
curl "http://localhost:8000/api/transactions/main.beancount:972"

# 更新交易
curl -X PUT "http://localhost:8000/api/transactions/main.beancount:972" \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-08-04", "flag": "*", "narration": "更新后的描述", ...}'

# 删除交易
curl -X DELETE "http://localhost:8000/api/transactions/main.beancount:972"
```

### 响应示例
```json
{
  "date": "2025-08-04",
  "flag": "*",
  "payee": null,
  "narration": "杭州-上海",
  "tags": [],
  "links": [],
  "postings": [...],
  "filename": "/path/to/main.beancount",
  "lineno": 972,
  "transaction_id": "main.beancount:972"
}
```

## 注意事项

### 1. 文件修改影响
- 如果手动修改 Beancount 文件，可能会影响行号的准确性
- 建议通过 API 进行交易的增删改操作

### 2. 多行交易处理
- 当前实现简化了多行交易的处理
- 复杂的多行交易可能需要更精细的行号管理

### 3. 备份和恢复
- 删除操作采用注释方式，保持行号的一致性
- 避免直接删除行导致行号偏移

## 总结

通过引入文件名+行号的唯一性标识，我们成功实现了：
1. 更稳定的交易记录标识方式
2. 更好的数据追溯能力
3. 与 Fava 兼容的实现方案
4. 完整的 CRUD API 支持

这个改进为 Beancount Web 系统提供了更可靠的交易管理基础设施。
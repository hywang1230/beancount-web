# 登录功能设置说明

本系统已集成单用户登录功能，未登录用户将无法访问应用。

## 默认登录信息

- **用户名**: `admin`
- **密码**: `admin123`

## 自定义登录信息

### 方式1: 环境变量
在启动应用前设置环境变量：

```bash
export USERNAME=your_username
export PASSWORD=your_password
export SECRET_KEY=your-secret-key
```

### 方式2: .env 配置文件
1. 在 `backend/` 目录下创建 `.env` 文件
2. 参考 `backend/user_config.example.env` 文件内容
3. 设置您的用户名和密码：

```env
SECRET_KEY=your-secret-key-change-this-in-production
USERNAME=your_username
PASSWORD=your_password
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

### 方式3: 直接修改配置文件
编辑 `backend/app/core/config.py` 文件中的相关配置：

```python
# 单用户登录配置
username: str = "your_username"
password: str = "your_password"
```

## 安全建议

1. **生产环境请务必修改默认密码**
2. **建议使用强密码**
3. **SECRET_KEY 请使用随机字符串**
4. **可以通过环境变量设置敏感信息，避免在代码中硬编码**

## 启动应用

设置完成后，按正常方式启动应用：

```bash
# 后端
cd backend
python main.py

# 前端
cd frontend  
npm run dev
```

应用启动后，访问任何页面都会自动跳转到登录页面。

## Token 有效期

默认 Token 有效期为 7 天 (10080 分钟)，可通过 `ACCESS_TOKEN_EXPIRE_MINUTES` 环境变量或配置文件调整。

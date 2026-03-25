# 更新日志

## 2026-03-25

### 功能更新：用户表添加 uid 字段

**变更内容：**
1. 用户表新增 `uid` 字段（UUID 类型），作为用户的唯一标识
2. `id` 保留为数据库主键，但不再用于业务逻辑
3. JWT token 的 `sub` 字段改为使用 `uid` 而非 `id`

**修改文件：**
- `api/models/user.py` - User 模型添加 uid 字段，自动生成 UUID
- `api/schemas/user.py` - UserResponse 添加 uid 字段
- `api/routers/auth.py` - create_access_token 使用 uid
- `api/deps.py` - 认证逻辑改为通过 uid 查询用户

**数据库迁移：**
- 后端启动时会自动为现有用户生成 uid
- 新用户创建时自动生成 uid

---

### Bug修复：管理端 API 401 未授权错误

**问题描述：**
- 管理端 Dashboard 页面调用 `/api/admin/stats` 返回 401 未授权

**根本原因：**
PyJWT 2.x 要求 JWT payload 中的 `sub` (subject) 字段必须是字符串类型，但代码中使用的是整数类型的 `user.id`，导致解码时报错 `InvalidSubjectError: Subject must be a string`

**解决方案：**
1. 修改 `api/routers/auth.py` 中的 `create_access_token` 函数，将 `user.id` 转为字符串：`str(user.id)`
2. 修改 `api/deps.py` 中的认证逻辑，在 JWT 解码后显式将 `user_id` 转换为整数类型

**修改文件：**
- `api/routers/auth.py`
- `api/deps.py`

---

## 2026-03-24

### Bug修复：favicon.ico 404 错误

**问题描述：**
- 访问管理端页面时，浏览器请求 `/favicon.ico` 返回 404 错误
- 原因：前端项目缺少 `public/` 目录和 `favicon.ico` 文件，且 `index.html` 未引用 favicon

**解决方案：**
1. 创建 `frontend/admin/public/` 和 `frontend/user/public/` 目录
2. 在两个前端项目的 `index.html` 中添加 favicon 引用：
   ```html
   <link rel="icon" type="image/x-icon" href="/favicon.ico">
   ```

**待完成：**
- 需要在 `frontend/admin/public/` 和 `frontend/user/public/` 目录中放置实际的 `favicon.ico` 文件
- 重新构建前端项目：`cd frontend/admin && npm run build`
- 部署更新后的 dist 目录到服务器

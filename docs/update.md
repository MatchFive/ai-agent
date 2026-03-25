# 更新日志

## 2026-03-25

### Bug修复：管理端 API 401 未授权错误

**问题描述：**
- 管理端 Dashboard 页面调用 `/api/admin/stats` 返回 401 未授权
- 原因：JWT 解码后 `user_id` 从 JSON 中取出时可能是字符串类型，导致数据库查询失败

**解决方案：**
- 修改 `api/deps.py` 中的认证逻辑，在 JWT 解码后显式将 `user_id` 转换为整数类型
- 同时修复 `get_current_user` 和 `get_optional_user` 两个函数

**修改文件：**
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

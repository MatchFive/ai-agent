# 更新日志

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

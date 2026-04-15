# 图片搜索功能配置与测试指南

## 📋 配置完成

你的 API Key 已经配置在 `.env` 文件中：

```env
IMAGE_PROVIDER=pexels
PEXELS_API_KEY=65j3g90BSfjoy1Sm9BzG5oybhVabsuSsb1QsUnWeIapaCtvLCcmqinQl
PIXABAY_API_KEY=55417186-2be9a96162f99759f060d9891
```

---

## 🧪 测试方法

### 方法一：快速测试（推荐）

测试所有 API 是否正常工作：

```bash
python test_image_quick.py
```

**输出示例：**
```
================================================================================
图片搜索快速测试
================================================================================

当前配置:
  提供商: pexels
  Pexels Key: ✓ 已配置
  Pixabay Key: ✓ 已配置

测试关键词: technology
--------------------------------------------------------------------------------

[1] Unsplash 测试:
   URL: https://source.unsplash.com/1200x600/?technology
   ✓ Unsplash 无需 API Key，直接可用

[2] Pexels 测试:
   ✓ 找到图片: https://images.pexels.com/photos/...
   摄影师: John Doe

[3] Pixabay 测试:
   ✓ 找到图片: https://pixabay.com/get/...
   用户: Jane Smith

================================================================================
配置验证:
  ✓ 当前使用 Pexels，配置正确
================================================================================
```

---

### 方法二：完整测试

运行详细的对比测试，生成测试报告：

```bash
python test_image_search.py
```

**测试模式：**
1. 快速测试（单个关键词）
2. 完整测试（多个关键词对比）
3. 自定义关键词测试

**测试报告：**
测试完成后会生成 `test_image_search_report.md` 文件，包含：
- 统计信息
- 详细测试结果
- 成功率对比

---

## 🎨 实际使用

### 在 generate_markdown.py 中使用

```python
# 默认使用 Pexels（已在 .env 中配置）
python generate_markdown.py
```

### 切换图片提供商

编辑 `.env` 文件：

```env
# 使用 Pexels（推荐）
IMAGE_PROVIDER=pexels

# 或使用 Pixabay
IMAGE_PROVIDER=pixabay

# 或使用 Unsplash（无需 API Key）
IMAGE_PROVIDER=unsplash
```

---

## 📊 API 对比

| 特性 | Unsplash | Pexels | Pixabay |
|------|----------|--------|---------|
| **API Key** | 不需要 | 需要（免费） | 需要（免费） |
| **图片质量** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **搜索精准度** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **图片数量** | 中等 | 多 | 非常多 |
| **响应速度** | 快 | 快 | 快 |
| **商用许可** | ✓ | ✓ | ✓ |
| **推荐指数** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**推荐使用：Pexels**（已配置）

---

## 🔧 常见问题

### Q1: 如何获取更多 API Key？

**Pexels:**
1. 访问 https://www.pexels.com/api/
2. 注册账号
3. 获取免费 API Key

**Pixabay:**
1. 访问 https://pixabay.com/api/docs/
2. 注册账号
3. 获取免费 API Key

### Q2: API Key 无效怎么办？

1. 检查 `.env` 文件中的 Key 是否正确
2. 运行 `python test_image_quick.py` 测试
3. 如果失败，尝试重新申请 API Key

### Q3: 如何测试生成的 Markdown？

```bash
# 生成测试 Markdown
python generate_markdown.py

# 查看生成的文件
# 文件位置: markdown_output/*.md
```

### Q4: 图片搜索失败怎么办？

系统会自动回退到 Unsplash：
- Pexels 失败 → 使用 Unsplash
- Pixabay 失败 → 使用 Unsplash
- 确保至少有一张图片可用

---

## 📝 测试检查清单

- [ ] 运行 `python test_image_quick.py`
- [ ] 确认 Pexels API 正常工作
- [ ] 确认 Pixabay API 正常工作
- [ ] 运行 `python generate_markdown.py` 生成测试文章
- [ ] 检查生成的 Markdown 文件是否包含配图
- [ ] 确认图片 URL 可访问

---

## 🚀 下一步

1. **测试图片搜索**
   ```bash
   python test_image_quick.py
   ```

2. **生成测试文章**
   ```bash
   python generate_markdown.py
   ```

3. **查看生成的文章**
   - 位置：`markdown_output/*.md`
   - 检查是否包含多张配图

4. **调整配置**
   - 编辑 `.env` 文件
   - 切换 `IMAGE_PROVIDER` 测试不同效果

---

**配置完成！现在可以开始测试了。** 🎉

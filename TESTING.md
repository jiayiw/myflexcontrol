# FlexRadio 6400 Control - 测试文档

## 测试概览

本项目包含完整的单元测试和集成测试套件，确保代码质量和功能稳定性。

### 测试框架

- **pytest** - 主要测试框架
- **pytest-mock** - Mock 支持
- **pytest-qt** - GUI 测试支持
- **pytest-cov** - 代码覆盖率
- **pytest-asyncio** - 异步测试支持

## 测试结构

```
tests/
├── conftest.py                    # 共享 fixtures 和配置
├── fixtures/                      # 测试数据
│   ├── mock_radio_responses.py   # 模拟无线电响应
│   └── sample_configs.py         # 测试配置
├── unit/                          # 单元测试
│   ├── test_flexradio_client.py  # 客户端网络层测试
│   ├── test_flexradio_api.py     # API 层测试
│   ├── test_config_manager.py    # 配置管理测试
│   ├── test_memory_manager.py    # 存储管理测试
│   └── test_audio_manager.py     # 音频管理测试
└── integration/                   # 集成测试
    ├── test_flexradio_gui.py     # GUI 关键路径测试
    └── test_e2e_flow.py          # 端到端流程测试
```

## 安装测试依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装测试依赖
pip install -r requirements-test.txt
```

## 运行测试

### 运行所有测试

```bash
# Linux/Mac
./run_tests.sh

# Windows
run_tests.bat
```

### 运行特定测试

```bash
# 运行所有测试
pytest tests/ -v

# 只运行单元测试
pytest tests/unit/ -v

# 只运行集成测试
pytest tests/integration/ -v -m integration

# 运行特定测试文件
pytest tests/unit/test_flexradio_api.py -v

# 运行特定测试函数
pytest tests/unit/test_flexradio_api.py::TestFlexRadioAPI::test_set_frequency -v
```

### 运行带覆盖率的测试

```bash
# 带覆盖率报告
pytest tests/ --cov=. --cov-report=term-missing --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html  # Mac/Linux
start htmlcov/index.html # Windows
```

### 运行特定标记的测试

```bash
# 跳过慢速测试
pytest tests/ -m "not slow"

# 只运行集成测试
pytest tests/ -m integration

# 只运行异步测试
pytest tests/ -m asyncio
```

## 测试覆盖范围

### 单元测试

#### 1. FlexRadioClient (test_flexradio_client.py)
- ✅ 初始化
- ✅ TCP 连接建立/断开
- ✅ 命令发送和响应接收
- ✅ 超时处理
- ✅ 心跳和状态消息解析

#### 2. FlexRadioAPI (test_flexradio_api.py)
- ✅ API 连接
- ✅ Slice 创建/删除
- ✅ 频率设置/获取
- ✅ 模式切换 (USB/LSB)
- ✅ RF/AF 增益控制
- ✅ PTT 开关
- ✅ Panadapter 启用/禁用
- ✅ 音频流启用
- ✅ 状态回调机制
- ✅ 状态更新处理

#### 3. ConfigManager (test_config_manager.py)
- ✅ 默认配置加载
- ✅ 配置文件读写
- ✅ 配置项获取/设置
- ✅ 配置合并逻辑
- ✅ 深度嵌套配置

#### 4. MemoryManager (test_memory_manager.py)
- ✅ 存储信道添加/删除/更新
- ✅ 配置序列化/反序列化
- ✅ 边界条件（最大信道数等）
- ✅ 无效数据处理

#### 5. AudioManager (test_audio_manager.py)
- ✅ 输入设备枚举
- ✅ 设备选择
- ✅ RX/TX 流启动/停止
- ✅ 清理逻辑
- ✅ 音频回调处理

### 集成测试

#### 1. GUI 测试 (test_flexradio_gui.py)
- ✅ 窗口初始化
- ✅ 频率输入处理
- ✅ 模式切换 UI 响应
- ✅ 增益滑块交互
- ✅ PTT 按钮和快捷键
- ✅ 存储信道召回
- ✅ 波段切换
- ✅ 状态显示
- ✅ 设置对话框

#### 2. 端到端测试 (test_e2e_flow.py)
- ✅ 完整连接流程
- ✅ 调谐和发射流程
- ✅ 存储信道保存和召回
- ✅ 错误处理和重连
- ✅ 多次频率更改
- ✅ 并发状态更新

## Mock 策略

### 硬件模拟
- 所有 FlexRadio TCP 通信用 `AsyncMock` 替代
- 无线电响应使用预定义的测试数据

### 音频设备
- PyAudio 初始化和设备枚举用 `Mock` 替代
- 音频流操作用模拟数据

### 异步代码
- 转为同步测试，用 `AsyncMock` 模拟异步结果
- 使用 `pytest-asyncio` 标记异步测试

### 文件系统
- 配置文件读写使用临时目录 (`tmp_path`)
- 使用 `temp_config_dir` fixture

## 测试最佳实践

### 1. 测试隔离
- 每个测试独立，不依赖执行顺序
- 使用 fixtures 提供测试数据
- 清理测试产生的资源

### 2. Mock 使用
- 对外部依赖使用 mock
- 模拟网络、文件系统、硬件设备
- 避免测试依赖外部环境

### 3. 测试命名
- 使用描述性测试名称
- 遵循 `test_<功能>_<场景>` 格式
- 例如：`test_connect_success`, `test_set_frequency`

### 4. 断言
- 使用明确的断言
- 验证状态变化
- 检查边界条件

### 5. 错误处理
- 测试错误场景
- 验证异常抛出
- 检查错误恢复

## 测试覆盖率目标

- **核心业务逻辑**: 80%+
- **API 层**: 75%+
- **GUI 交互**: 60%+
- **总体**: 70%+

## 调试测试

### 显示打印输出

```bash
pytest tests/ -s
```

### 进入调试器

```bash
pytest tests/ --pdb
```

### 详细输出

```bash
pytest tests/ -vv
```

### 只运行失败的测试

```bash
pytest tests/ --lf
```

## 持续集成

测试可以在 CI/CD 环境中运行：

```bash
# 安装依赖
pip install -r requirements.txt
pip install -r requirements-test.txt

# 运行测试
pytest tests/ --cov=. --cov-report=xml

# 生成覆盖率报告
codecov
```

## 常见问题

### 1. GUI 测试失败

确保设置了正确的显示环境：

```bash
# Linux
export QT_QPA_PLATFORM=offscreen

# 或使用 Xvfb
xvfb-run pytest tests/integration/test_flexradio_gui.py
```

### 2. 异步测试超时

增加超时时间：

```bash
pytest tests/ --timeout=60
```

### 3. Mock 不生效

确保 mock 的导入路径正确：

```python
# 正确
with patch('module.function'):
    ...

# 错误
with patch('other_module.function'):
    ...
```

### 4. 测试数据库冲突

使用临时目录：

```python
def test_config(temp_config_dir):
    # 使用 temp_config_dir
    ...
```

## 扩展测试

### 添加新测试

1. 在适当的目录创建测试文件
2. 使用 `test_` 前缀命名文件和函数
3. 导入必要的 fixtures
4. 编写测试用例

### 示例测试

```python
import pytest
from unittest.mock import Mock

def test_new_feature():
    """测试新功能"""
    # 准备
    obj = MyClass()
    
    # 执行
    result = obj.new_feature()
    
    # 验证
    assert result == expected_value
```

## 测试维护

### 定期更新

1. 添加新功能时同步添加测试
2. 修复 bug 时添加回归测试
3. 重构代码时更新测试
4. 定期检查测试覆盖率

### 测试质量

1. 保持测试简单明了
2. 避免过度 mock
3. 测试行为而非实现
4. 保持测试可维护

## 相关资源

- [pytest 文档](https://docs.pytest.org/)
- [pytest-qt 文档](https://pytest-qt.readthedocs.io/)
- [pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov 文档](https://pytest-cov.readthedocs.io/)

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。
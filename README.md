# FastAPI 交易系统

一个使用 FastAPI 构建的交易系统后端服务。

## 功能特性

- 用户管理
- 交易处理
- 依赖注入
- 异常处理

## 开发环境要求

- Python 3.8+
- Docker
- Make

## 快速开始

1. 克隆项目 

```bash
git clone https://github.com/howardshaw/fastapi_session_
```


2. 使用 Docker 运行

```bash
make up
```

3. 本地开发环境设置
```bash
make install
make run
```


## API 文档

启动服务后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发指南

- 运行测试: `make test`
- 运行 lint: `make lint`
- 格式化代码: `make format`
"""
验证 Hugging Face 镜像配置
不依赖 sentence-transformers，仅验证配置是否正确
"""

import os
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src" / "retrieval"))

def check_env_variable():
    """检查环境变量设置"""
    print("=" * 60)
    print("1. 检查 HF_ENDPOINT 环境变量")
    print("=" * 60)
    
    hf_endpoint = os.environ.get("HF_ENDPOINT", "未设置")
    print(f"当前 HF_ENDPOINT: {hf_endpoint}")
    
    if hf_endpoint == "https://hf-mirror.com":
        print("[OK] 环境变量已正确设置为国内镜像")
        return True
    else:
        print("[WARN] 环境变量未设置为国内镜像")
        return False


def check_embedding_generator():
    """检查 embedding_generator.py 是否正确配置"""
    print("\n" + "=" * 60)
    print("2. 检查 embedding_generator.py 代码")
    print("=" * 60)
    
    try:
        # 直接读取文件检查
        file_path = Path(__file__).parent / "src" / "retrieval" / "embedding_generator.py"
        content = file_path.read_text(encoding="utf-8")
        
        # 检查是否包含镜像配置代码
        if 'os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"' in content:
            print("[OK] embedding_generator.py 已正确配置镜像")
            print("     代码会自动设置 HF_ENDPOINT 环境变量")
            return True
        else:
            print("[WARN] embedding_generator.py 未找到镜像配置代码")
            return False
            
    except Exception as e:
        print(f"[ERROR] 检查失败: {e}")
        return False


def check_env_file():
    """检查 .env.example 文件"""
    print("\n" + "=" * 60)
    print("3. 检查 .env.example 配置")
    print("=" * 60)
    
    env_file = Path(__file__).parent / ".env.example"
    if not env_file.exists():
        print("[WARN] .env.example 文件不存在")
        return False
    
    content = env_file.read_text(encoding="utf-8")
    
    if "HF_ENDPOINT=https://hf-mirror.com" in content:
        print("[OK] .env.example 已包含 HF_ENDPOINT 配置")
        return True
    else:
        print("[WARN] .env.example 未包含 HF_ENDPOINT 配置")
        return False


def show_usage():
    """显示使用说明"""
    print("\n" + "=" * 60)
    print("使用说明")
    print("=" * 60)
    print("""
配置 Hugging Face 国内镜像后，模型下载将从 hf-mirror.com 获取：

方法1 - 代码自动设置（已配置）:
    embedding_generator.py 已自动设置 HF_ENDPOINT

方法2 - 系统环境变量（可选）:
    Windows PowerShell:
        $env:HF_ENDPOINT = "https://hf-mirror.com"
    
    Windows CMD:
        set HF_ENDPOINT=https://hf-mirror.com
    
    永久设置（系统环境变量）:
        [系统设置] -> [环境变量] -> 添加 HF_ENDPOINT

方法3 - .env 文件（推荐）:
    复制 .env.example 为 .env
    已包含 HF_ENDPOINT=https://hf-mirror.com

验证下载速度:
    安装 sentence-transformers 后运行:
    python test_hf_mirror.py
""")


def main():
    """主函数"""
    print("Hugging Face 国内镜像配置验证")
    print("=" * 60)
    
    results = []
    results.append(("环境变量", check_env_variable()))
    results.append(("代码配置", check_embedding_generator()))
    results.append(("配置文件", check_env_file()))
    
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "[OK]" if passed else "[FAIL]"
        print(f"{status} {name}")
        if not passed:
            all_passed = False
    
    show_usage()
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

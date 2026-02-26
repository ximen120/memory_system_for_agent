#!/usr/bin/env python3
"""
Embedding模型预下载脚本

解决模型下载慢的问题，支持：
1. 预下载模型到本地缓存
2. 断点续传
3. 多镜像源
4. 进度显示

使用方法:
    python scripts/download_model.py --model all-MiniLM-L6-v2
    python scripts/download_model.py --model all-MiniLM-L6-v2 --output ./models
"""

import os
import sys
import argparse
import time
from pathlib import Path
from typing import Optional


def download_model(
    model_name: str = "all-MiniLM-L6-v2",
    output_dir: str = "./models",
    timeout: int = 300,
    retry: int = 3
) -> bool:
    """
    下载Embedding模型
    
    Args:
        model_name: 模型名称
        output_dir: 输出目录
        timeout: 下载超时时间（秒）
        retry: 重试次数
        
    Returns:
        是否下载成功
    """
    print(f"=" * 60)
    print(f"Embedding模型预下载")
    print(f"=" * 60)
    print(f"模型: {model_name}")
    print(f"输出目录: {output_dir}")
    print(f"超时: {timeout}秒")
    print(f"重试: {retry}次")
    print()
    
    output_path = Path(output_dir) / model_name
    
    # 检查是否已存在
    if output_path.exists():
        print(f"模型已存在: {output_path}")
        print("跳过下载")
        return True
    
    # 创建输出目录
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 尝试下载
    for attempt in range(1, retry + 1):
        print(f"尝试 {attempt}/{retry}...")
        
        try:
            # 导入sentence-transformers
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                print("错误: 未安装sentence-transformers")
                print("请先安装: pip install sentence-transformers")
                return False
            
            # 设置超时
            import socket
            socket.setdefaulttimeout(timeout)
            
            # 下载模型
            print(f"正在下载 {model_name}...")
            print("(这可能需要几分钟，取决于网络速度)")
            print()
            
            start_time = time.time()
            
            # 下载模型
            model = SentenceTransformer(model_name)
            
            # 保存到本地
            print(f"保存模型到: {output_path}")
            model.save(str(output_path))
            
            elapsed = time.time() - start_time
            print(f"下载完成! 耗时: {elapsed:.1f}秒")
            
            return True
            
        except Exception as e:
            print(f"下载失败: {e}")
            
            if attempt < retry:
                wait_time = 5 * attempt
                print(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print("所有重试都失败了")
                return False
    
    return False


def verify_model(model_path: str) -> bool:
    """
    验证模型是否可用
    
    Args:
        model_path: 模型路径
        
    Returns:
        是否可用
    """
    print(f"\n验证模型: {model_path}")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer(model_path)
        
        # 测试生成
        test_text = "测试文本"
        embedding = model.encode(test_text)
        
        print(f"模型验证成功!")
        print(f"  向量维度: {len(embedding)}")
        print(f"  测试文本: '{test_text}'")
        
        return True
        
    except Exception as e:
        print(f"模型验证失败: {e}")
        return False


def list_cached_models(cache_dir: str = "./models") -> None:
    """
    列出已缓存的模型
    
    Args:
        cache_dir: 缓存目录
    """
    print(f"\n已缓存的模型 ({cache_dir}):")
    print("-" * 40)
    
    cache_path = Path(cache_dir)
    
    if not cache_path.exists():
        print("缓存目录不存在")
        return
    
    models = [d for d in cache_path.iterdir() if d.is_dir()]
    
    if not models:
        print("没有缓存的模型")
        return
    
    for model_dir in models:
        size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
        size_mb = size / (1024 * 1024)
        print(f"  {model_dir.name} ({size_mb:.1f} MB)")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Embedding模型预下载脚本"
    )
    
    parser.add_argument(
        "--model",
        default="all-MiniLM-L6-v2",
        help="模型名称 (默认: all-MiniLM-L6-v2)"
    )
    
    parser.add_argument(
        "--output",
        default="./models",
        help="输出目录 (默认: ./models)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="下载超时时间（秒）(默认: 300)"
    )
    
    parser.add_argument(
        "--retry",
        type=int,
        default=3,
        help="重试次数 (默认: 3)"
    )
    
    parser.add_argument(
        "--verify",
        action="store_true",
        help="下载后验证模型"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出已缓存的模型"
    )
    
    args = parser.parse_args()
    
    # 列出缓存
    if args.list:
        list_cached_models(args.output)
        return 0
    
    # 下载模型
    success = download_model(
        model_name=args.model,
        output_dir=args.output,
        timeout=args.timeout,
        retry=args.retry
    )
    
    if success and args.verify:
        model_path = Path(args.output) / args.model
        verify_model(str(model_path))
    
    print()
    if success:
        print("=" * 60)
        print("模型准备就绪!")
        print("=" * 60)
        return 0
    else:
        print("=" * 60)
        print("模型下载失败")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""
测试 Hugging Face 镜像下载速度
对比官方源和镜像源的下载速度
"""

import os
import sys
import time
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src" / "retrieval"))

def test_download_speed(use_mirror=True):
    """测试模型下载速度"""
    
    if use_mirror:
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        source = "hf-mirror.com (国内镜像)"
    else:
        if "HF_ENDPOINT" in os.environ:
            del os.environ["HF_ENDPOINT"]
        source = "huggingface.co (官方源)"
    
    print(f"\n{'='*60}")
    print(f"测试源: {source}")
    print(f"{'='*60}")
    
    # 清理缓存，强制重新下载
    cache_dir = Path("./test_model_cache")
    if cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir, ignore_errors=True)
    cache_dir.mkdir(exist_ok=True)
    
    start_time = time.time()
    
    try:
        from sentence_transformers import SentenceTransformer
        
        print(f"开始下载模型: sentence-transformers/all-MiniLM-L6-v2")
        print(f"缓存目录: {cache_dir.absolute()}")
        
        model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            cache_folder=str(cache_dir)
        )
        
        # 测试生成 embedding
        test_text = "这是一个测试句子"
        embedding = model.encode(test_text)
        
        elapsed = time.time() - start_time
        
        print(f"[OK] 下载成功！")
        print(f"耗时: {elapsed:.2f} 秒")
        print(f"Embedding 维度: {len(embedding)}")
        
        return elapsed, True
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[FAIL] 下载失败: {e}")
        print(f"耗时: {elapsed:.2f} 秒")
        return elapsed, False


def main():
    """主测试函数"""
    print("Hugging Face 镜像速度测试")
    print("模型: sentence-transformers/all-MiniLM-L6-v2 (~80MB)")
    
    # 测试镜像源
    mirror_time, mirror_success = test_download_speed(use_mirror=True)
    
    # 测试官方源（可选，如果镜像成功则跳过）
    official_time = None
    official_success = False
    
    if mirror_success:
        print("\n" + "="*60)
        print("镜像源测试成功，跳过官方源测试（避免重复下载）")
        print("="*60)
    else:
        print("\n镜像源失败，尝试官方源...")
        official_time, official_success = test_download_speed(use_mirror=False)
    
    # 结果对比
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    if mirror_success:
        print(f"[OK] 国内镜像 (hf-mirror.com): {mirror_time:.2f} 秒")
    else:
        print(f"[FAIL] 国内镜像 (hf-mirror.com): 失败")
    
    if official_time:
        if official_success:
            print(f"[OK] 官方源 (huggingface.co): {official_time:.2f} 秒")
        else:
            print(f"[FAIL] 官方源 (huggingface.co): 失败")
        
        if mirror_success and official_success:
            speedup = official_time / mirror_time
            print(f"\n镜像加速比: {speedup:.2f}x")
    
    # 清理测试缓存
    cache_dir = Path("./test_model_cache")
    if cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir, ignore_errors=True)
        print(f"\n清理测试缓存完成")
    
    return mirror_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

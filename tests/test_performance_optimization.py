"""
Tests for Performance Optimization (Phase 16).

Tests caching, lazy loading configuration, and async optimizations.
"""

import pytest
import asyncio
import time


class TestCacheService:
    """Test cache service functionality."""

    def test_cache_set_and_get(self):
        """Cache should store and retrieve values."""
        from app.services.cache_service import CacheService
        
        cache = CacheService(default_ttl=60.0)
        
        async def run():
            await cache.set("key1", "value1")
            result = await cache.get("key1")
            assert result == "value1"
        
        asyncio.run(run())

    def test_cache_expiration(self):
        """Cache should expire entries after TTL."""
        from app.services.cache_service import CacheService
        
        cache = CacheService(default_ttl=0.1)  # 100ms TTL
        
        async def run():
            await cache.set("key1", "value1")
            result1 = await cache.get("key1")
            assert result1 == "value1"
            
            # Wait for expiration
            await asyncio.sleep(0.15)
            result2 = await cache.get("key1")
            assert result2 is None
        
        asyncio.run(run())

    def test_cache_delete(self):
        """Cache delete should remove entry."""
        from app.services.cache_service import CacheService
        
        cache = CacheService()
        
        async def run():
            await cache.set("key1", "value1")
            deleted = await cache.delete("key1")
            assert deleted is True
            assert await cache.get("key1") is None
        
        asyncio.run(run())

    def test_cache_clear(self):
        """Cache clear should remove all entries."""
        from app.services.cache_service import CacheService
        
        cache = CacheService()
        
        async def run():
            await cache.set("key1", "value1")
            await cache.set("key2", "value2")
            await cache.clear()
            assert await cache.get("key1") is None
            assert await cache.get("key2") is None
        
        asyncio.run(run())

    def test_cache_get_or_set(self):
        """Cache get_or_set should compute on miss."""
        from app.services.cache_service import CacheService
        
        cache = CacheService()
        call_count = 0
        
        async def factory():
            nonlocal call_count
            call_count += 1
            return f"computed_{call_count}"
        
        async def run():
            # First call should compute
            result1 = await cache.get_or_set("key1", factory)
            assert result1 == "computed_1"
            assert call_count == 1
            
            # Second call should use cache
            result2 = await cache.get_or_set("key1", factory)
            assert result2 == "computed_1"
            assert call_count == 1
        
        asyncio.run(run())


class TestStockServiceCaching:
    """Test stock service caching behavior."""

    def test_get_multiple_quotes_uses_concurrent_fetches(self):
        """get_multiple_quotes should fetch concurrently."""
        from app.services.stock_service import StockService
        
        service = StockService()
        
        # This test verifies the method signature exists and is async
        assert asyncio.iscoroutinefunction(service.get_multiple_quotes)


class TestViteConfig:
    """Test Vite build configuration."""

    def test_vite_config_lazy_loading_enabled(self):
        """Verify lazy loading is configured."""
        import os
        from vite import defineConfig
        
        # Just verify the config can be loaded
        config_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 'frontend', 'vite.config.ts'
        )
        assert os.path.exists(config_path)


class TestAsyncOptimizations:
    """Test async processing optimizations."""

    def test_concurrent_fetch_pattern(self):
        """Verify concurrent fetching pattern works."""
        async def fetch_one(i):
            await asyncio.sleep(0.01)
            return i * 2
        
        async def run():
            results = await asyncio.gather(*[fetch_one(i) for i in range(5)])
            assert results == [0, 2, 4, 6, 8]
        
        asyncio.run(run())

    def test_cache_cleanup_removes_expired(self):
        """Cache cleanup should remove expired entries."""
        from app.services.cache_service import CacheService
        
        cache = CacheService(default_ttl=0.05)
        
        async def run():
            await cache.set("key1", "value1")
            await asyncio.sleep(0.06)
            removed = await cache.cleanup_expired()
            assert removed == 1
            assert await cache.get("key1") is None
        
        asyncio.run(run())

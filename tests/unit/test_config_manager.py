from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from config_manager import ConfigManager


class TestConfigManager:
    """测试配置管理器"""

    def test_load_default_config(self, temp_config_dir):
        """测试加载默认配置"""
        with patch.object(Path, "home", return_value=temp_config_dir.parent):
            manager = ConfigManager()

            assert "radio" in manager.config
            assert "display" in manager.config
            assert "audio" in manager.config
            assert "memory" in manager.config
            assert manager.get_radio_ip() == "192.168.1.100"

    def test_load_custom_config(self, temp_config_dir, sample_config):
        """测试加载自定义配置"""
        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        with patch.object(Path, "home", return_value=temp_config_dir.parent):
            manager = ConfigManager()

            assert manager.get_radio_ip() == "192.168.1.100"
            assert manager.get("audio.sample_rate") == 48000
            assert manager.get("memory.max_channels") == 10

    def test_save_config(self, temp_config_dir, sample_config):
        """测试保存配置"""
        with patch.object(Path, "home", return_value=temp_config_dir.parent):
            manager = ConfigManager()
            manager.config = sample_config
            manager.save_config()

            config_file = manager.config_file
            assert config_file.exists()

            with open(config_file) as f:
                loaded = yaml.safe_load(f)
                assert loaded["radio"]["ip_address"] == "192.168.1.100"
                assert loaded["audio"]["sample_rate"] == 48000

    def test_get_nested_value(self, temp_config_dir):
        """测试获取嵌套配置值"""
        with patch.object(Path, "home", return_value=temp_config_dir.parent):
            manager = ConfigManager()

            assert manager.get("radio.tcp_port") == 4992
            assert manager.get("radio.udp_port") == 4991
            assert manager.get("display.panadapter_width", 1024) == 1024
            assert manager.get("audio.sample_rate") == 48000
            assert manager.get("nonexistent.key", "default") == "default"
            assert manager.get("radio.nonexistent", "test") == "test"

    def test_set_nested_value(self, temp_config_dir):
        """测试设置嵌套配置值"""
        with patch.object(Path, "home", return_value=temp_config_dir.parent):
            manager = ConfigManager()

            manager.set("radio.ip_address", "192.168.1.200")
            assert manager.get_radio_ip() == "192.168.1.200"

            manager.set("audio.sample_rate", 96000)
            assert manager.get("audio.sample_rate") == 96000

            manager.set("display.panadapter_fps", 30)
            assert manager.get("display.panadapter_fps") == 30

    def test_get_radio_ip(self, temp_config_dir):
        """测试获取无线电 IP"""
        with patch.object(Path, "home", return_value=temp_config_dir.parent):
            manager = ConfigManager()

            ip = manager.get_radio_ip()
            assert ip == "192.168.1.100"

    def test_set_radio_ip(self, temp_config_dir):
        """测试设置无线电 IP"""
        with patch.object(Path, "home", return_value=temp_config_dir.parent):
            manager = ConfigManager()

            manager.set_radio_ip("192.168.1.200")
            assert manager.get_radio_ip() == "192.168.1.200"

            config_file = manager.config_file
            assert config_file.exists()

            with open(config_file) as f:
                loaded = yaml.safe_load(f)
                assert loaded["radio"]["ip_address"] == "192.168.1.200"

    def test_deep_merge(self, temp_config_dir):
        """测试配置深度合并"""
        with patch.object(Path, "home", return_value=temp_config_dir.parent):
            manager = ConfigManager()
            original_port = manager.get("radio.tcp_port")

            partial = {"radio": {"ip_address": "192.168.1.200"}}
            manager._deep_merge(partial, manager.config)

            assert manager.get_radio_ip() == "192.168.1.200"
            assert manager.get("radio.tcp_port") == original_port

    def test_deep_merge_multiple_levels(self, temp_config_dir):
        """测试多层嵌套配置合并"""
        with patch.object(Path, "home", return_value=temp_config_dir.parent):
            manager = ConfigManager()

            partial = {"audio": {"sample_rate": 96000, "channels": 2}}
            manager._deep_merge(partial, manager.config)

            assert manager.get("audio.sample_rate") == 96000
            assert manager.get("audio.channels") == 2
            assert manager.get("audio.chunk_size") == 1024

    def test_load_config_with_invalid_yaml(self, temp_config_dir):
        """测试加载无效的 YAML 文件"""
        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            f.write("invalid: yaml: content: [")

        with patch.object(Path, "home", return_value=temp_config_dir.parent):
            manager = ConfigManager()

            assert manager.config is not None
            assert "radio" in manager.config

    def test_get_with_empty_key(self, temp_config_dir):
        """测试获取空键"""
        with patch.object(Path, "home", return_value=temp_config_dir.parent):
            manager = ConfigManager()

            result = manager.get("", "default")
            assert result == "default"

    def test_set_creates_nested_structure(self, temp_config_dir):
        """测试设置值时创建嵌套结构"""
        with patch.object(Path, "home", return_value=temp_config_dir.parent):
            manager = ConfigManager()

            manager.set("new.nested.value", "test")

            assert manager.get("new.nested.value") == "test"
            assert "new" in manager.config
            assert "nested" in manager.config["new"]

    def test_save_config_with_none(self, temp_config_dir):
        """测试保存 None 配置"""
        with patch.object(Path, "home", return_value=temp_config_dir.parent):
            manager = ConfigManager()

            manager.save_config(None)

            config_file = manager.config_file
            assert config_file.exists()

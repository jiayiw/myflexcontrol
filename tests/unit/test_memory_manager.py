import pytest

from memory_manager import MemoryChannel, MemoryManager


class TestMemoryChannel:
    """测试存储信道数据类"""

    def test_init(self):
        """测试初始化"""
        channel = MemoryChannel(
            name="40m SSB", frequency=7150000, mode="usb", rf_gain=50, af_gain=50
        )

        assert channel.name == "40m SSB"
        assert channel.frequency == 7150000
        assert channel.mode == "usb"
        assert channel.rf_gain == 50
        assert channel.af_gain == 50

    def test_init_with_defaults(self):
        """测试使用默认值初始化"""
        channel = MemoryChannel(name="Test", frequency=14250000, mode="lsb")

        assert channel.name == "Test"
        assert channel.frequency == 14250000
        assert channel.mode == "lsb"
        assert channel.rf_gain == 50
        assert channel.af_gain == 50


class TestMemoryManager:
    """测试存储管理器"""

    def test_init(self):
        """测试初始化"""
        manager = MemoryManager(max_channels=10)

        assert manager.max_channels == 10
        assert len(manager.channels) == 0

    def test_init_default_max_channels(self):
        """测试默认最大信道数"""
        manager = MemoryManager()

        assert manager.max_channels == 10

    def test_add_channel(self):
        """测试添加存储信道"""
        manager = MemoryManager(max_channels=2)

        channel1 = MemoryChannel("40m SSB", 7150000, "usb", 50, 50)
        assert manager.add_channel(channel1) is True
        assert len(manager.channels) == 1

        channel2 = MemoryChannel("20m LSB", 14250000, "lsb", 60, 50)
        assert manager.add_channel(channel2) is True
        assert len(manager.channels) == 2

        channel3 = MemoryChannel("15m USB", 21250000, "usb", 55, 50)
        assert manager.add_channel(channel3) is False
        assert len(manager.channels) == 2

    def test_add_channel_to_max(self):
        """测试添加信道到最大数量"""
        manager = MemoryManager(max_channels=3)

        for i in range(3):
            channel = MemoryChannel(f"Channel {i}", 7150000 + i * 1000, "usb")
            assert manager.add_channel(channel) is True

        assert len(manager.channels) == 3

        channel4 = MemoryChannel("Channel 4", 7153000, "usb")
        assert manager.add_channel(channel4) is False

    def test_update_channel(self):
        """测试更新存储信道"""
        manager = MemoryManager()
        channel = MemoryChannel("40m SSB", 7150000, "usb", 50, 50)
        manager.add_channel(channel)

        updated = MemoryChannel("40m USB Updated", 7200000, "usb", 60, 55)
        assert manager.update_channel(0, updated) is True
        assert manager.channels[0].name == "40m USB Updated"
        assert manager.channels[0].frequency == 7200000
        assert manager.channels[0].rf_gain == 60

    def test_update_channel_invalid_index(self):
        """测试更新无效索引的信道"""
        manager = MemoryManager()
        channel = MemoryChannel("Test", 7150000, "usb")
        manager.add_channel(channel)

        updated = MemoryChannel("Updated", 7200000, "lsb")
        assert manager.update_channel(99, updated) is False
        assert manager.update_channel(-1, updated) is False

    def test_delete_channel(self):
        """测试删除存储信道"""
        manager = MemoryManager()
        channel = MemoryChannel("40m SSB", 7150000, "usb", 50, 50)
        manager.add_channel(channel)

        assert manager.delete_channel(0) is True
        assert len(manager.channels) == 0

    def test_delete_channel_invalid_index(self):
        """测试删除无效索引的信道"""
        manager = MemoryManager()

        assert manager.delete_channel(0) is False
        assert manager.delete_channel(99) is False
        assert manager.delete_channel(-1) is False

    def test_get_channel(self):
        """测试获取存储信道"""
        manager = MemoryManager()
        channel = MemoryChannel("40m SSB", 7150000, "usb", 50, 50)
        manager.add_channel(channel)

        result = manager.get_channel(0)
        assert result is not None
        assert result.name == "40m SSB"
        assert result.frequency == 7150000

    def test_get_channel_invalid_index(self):
        """测试获取无效索引的信道"""
        manager = MemoryManager()

        result = manager.get_channel(0)
        assert result is None

        result = manager.get_channel(99)
        assert result is None

        result = manager.get_channel(-1)
        assert result is None

    def test_all_channels(self):
        """测试获取所有信道"""
        manager = MemoryManager()

        channel1 = MemoryChannel("40m SSB", 7150000, "usb")
        channel2 = MemoryChannel("20m LSB", 14250000, "lsb")

        manager.add_channel(channel1)
        manager.add_channel(channel2)

        all_channels = manager.all_channels()

        assert len(all_channels) == 2
        assert all_channels[0].name == "40m SSB"
        assert all_channels[1].name == "20m LSB"

    def test_all_channels_empty(self):
        """测试获取空信道列表"""
        manager = MemoryManager()

        all_channels = manager.all_channels()

        assert len(all_channels) == 0
        assert all_channels == []

    def test_load_from_config(self, sample_config):
        """测试从配置加载"""
        manager = MemoryManager()
        manager.load_from_config(sample_config)

        assert len(manager.channels) == 2
        assert manager.channels[0].name == "40m SSB"
        assert manager.channels[0].frequency == 7150000
        assert manager.channels[0].mode == "usb"
        assert manager.channels[1].name == "20m Calling"
        assert manager.channels[1].frequency == 14250000
        assert manager.channels[1].mode == "lsb"

    def test_load_from_config_empty(self):
        """测试从空配置加载"""
        manager = MemoryManager()
        manager.load_from_config({})

        assert len(manager.channels) == 0

    def test_load_from_config_partial(self):
        """测试从部分配置加载"""
        manager = MemoryManager()
        config = {"memory": {"channels": [{"name": "Test", "frequency": 7150000, "mode": "usb"}]}}

        manager.load_from_config(config)

        assert len(manager.channels) == 1
        assert manager.channels[0].name == "Test"

    def test_load_from_config_invalid_channel(self):
        """测试加载无效信道数据"""
        manager = MemoryManager()
        config = {
            "memory": {
                "channels": [
                    {"name": "Valid", "frequency": 7150000, "mode": "usb"},
                    {"invalid": "data"},
                    {"name": "Missing Freq", "mode": "usb"},
                ]
            }
        }

        manager.load_from_config(config)

        assert len(manager.channels) == 1
        assert manager.channels[0].name == "Valid"

    def test_save_to_config(self):
        """测试保存到配置"""
        manager = MemoryManager()
        channel1 = MemoryChannel("40m SSB", 7150000, "usb", 50, 50)
        channel2 = MemoryChannel("20m LSB", 14250000, "lsb", 60, 55)

        manager.add_channel(channel1)
        manager.add_channel(channel2)

        config = manager.save_to_config()

        assert "memory" in config
        assert config["memory"]["max_channels"] == 10
        assert len(config["memory"]["channels"]) == 2
        assert config["memory"]["channels"][0]["name"] == "40m SSB"
        assert config["memory"]["channels"][0]["frequency"] == 7150000
        assert config["memory"]["channels"][1]["name"] == "20m LSB"
        assert config["memory"]["channels"][1]["frequency"] == 14250000

    def test_save_to_config_empty(self):
        """测试保存空配置"""
        manager = MemoryManager()

        config = manager.save_to_config()

        assert "memory" in config
        assert config["memory"]["max_channels"] == 10
        assert len(config["memory"]["channels"]) == 0

    def test_load_save_roundtrip(self, sample_config):
        """测试加载和保存的往返"""
        manager1 = MemoryManager()
        manager1.load_from_config(sample_config)

        config = manager1.save_to_config()

        manager2 = MemoryManager()
        manager2.load_from_config(config)

        assert len(manager2.channels) == len(manager1.channels)
        for i in range(len(manager1.channels)):
            assert manager2.channels[i].name == manager1.channels[i].name
            assert manager2.channels[i].frequency == manager1.channels[i].frequency
            assert manager2.channels[i].mode == manager1.channels[i].mode

    def test_multiple_operations(self):
        """测试多个操作组合"""
        manager = MemoryManager(max_channels=5)

        channel1 = MemoryChannel("40m", 7150000, "usb")
        channel2 = MemoryChannel("20m", 14250000, "lsb")
        channel3 = MemoryChannel("15m", 21250000, "usb")

        assert manager.add_channel(channel1) is True
        assert manager.add_channel(channel2) is True
        assert manager.add_channel(channel3) is True

        assert len(manager.channels) == 3

        updated = MemoryChannel("40m Updated", 7200000, "usb", 60)
        assert manager.update_channel(0, updated) is True

        assert manager.delete_channel(1) is True

        assert len(manager.channels) == 2
        assert manager.channels[0].name == "40m Updated"
        assert manager.channels[1].name == "15m"

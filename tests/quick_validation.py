#!/usr/bin/env python3
"""
Quick Infrastructure Validation

Simple validation script to verify Phase 1 infrastructure is operational.
"""

import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
tests_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "lib"))
sys.path.insert(0, str(tests_root))

def validate_imports():
    """Validate all mock framework imports"""
    try:
        from mocks.discord_mocks import create_mock_discord_bot
        from mocks.websocket_mocks import create_mock_websocket_server
        from mocks.github_mocks import create_mock_github_api
        from mocks.filesystem_mocks import create_mock_filesystem
        from mocks.async_fixtures import async_fixture_factory
        print("✅ All mock frameworks imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import validation failed: {e}")
        return False

def validate_basic_functionality():
    """Validate basic functionality of each framework"""
    try:
        from mocks.discord_mocks import create_mock_discord_bot
        from mocks.websocket_mocks import create_mock_websocket_server
        from mocks.github_mocks import create_mock_github_api
        from mocks.filesystem_mocks import create_mock_filesystem
        
        # Test Discord
        try:
            discord_bot = create_mock_discord_bot()
            initial_guilds = len(discord_bot.guilds)
            guild = discord_bot.add_mock_guild()
            assert len(discord_bot.guilds) == initial_guilds + 1
            print("✅ Discord mock framework functional")
        except Exception as e:
            print(f"❌ Discord mock framework failed: {e}")
            return False
        
        # Test WebSocket
        try:
            websocket_server = create_mock_websocket_server()
            assert websocket_server.host == "localhost"
            assert websocket_server.port == 8765
            print("✅ WebSocket mock framework functional")
        except Exception as e:
            print(f"❌ WebSocket mock framework failed: {e}")
            return False
        
        # Test GitHub
        try:
            github_api = create_mock_github_api()
            user = github_api.get_user()
            assert user.login == "authenticated_user"
            print("✅ GitHub mock framework functional")
        except Exception as e:
            print(f"❌ GitHub mock framework failed: {e}")
            return False
        
        # Test FileSystem
        try:
            filesystem = create_mock_filesystem()
            filesystem.write_text("/test.txt", "Hello, World!")
            content = filesystem.read_text("/test.txt")
            assert content == "Hello, World!"
            print("✅ FileSystem mock framework functional")
        except Exception as e:
            print(f"❌ FileSystem mock framework failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality validation failed: {e}")
        return False

def validate_mockagenbt():
    """Validate MockAgent fixes"""
    try:
        # Add lib to path and try importing the MockAgent
        sys.path.insert(0, str(project_root / "lib"))
        from agents.mock_agent import MockAgent
        
        # Create a mock agent
        agent = MockAgent("TestAgent")
        assert hasattr(agent, 'success_rate')
        assert agent.success_rate == 0.95
        print("✅ MockAgent fixes applied successfully")
        return True
        
    except Exception as e:
        print(f"❌ MockAgent validation failed: {e}")
        return False

def validate_pytest_config():
    """Validate pytest configuration"""
    try:
        import pytest
        
        # Check if pytest-asyncio is available
        import pytest_asyncio
        print("✅ pytest-asyncio available")
        
        # Check pytest.ini exists
        pytest_ini = Path(__file__).parent / "pytest.ini"
        if pytest_ini.exists():
            print("✅ pytest.ini configuration found")
        else:
            print("⚠️  pytest.ini not found")
            
        return True
        
    except ImportError:
        print("❌ pytest or pytest-asyncio not available")
        return False
    except Exception as e:
        print(f"❌ pytest configuration validation failed: {e}")
        return False

def main():
    """Run quick validation"""
    print("🚀 Quick Infrastructure Validation - Phase 1")
    print("=" * 60)
    
    tests = [
        ("Import Validation", validate_imports),
        ("Basic Functionality", validate_basic_functionality),
        ("MockAgent Fixes", validate_mockagenbt),
        ("Pytest Configuration", validate_pytest_config)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"   Failed: {test_name}")
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 PHASE 1 INFRASTRUCTURE: OPERATIONAL")
        print("✅ Ready for Phase 2 implementation")
        print("🎯 Target: 95%+ coverage for government audit compliance")
    else:
        print("⚠️  PHASE 1 INFRASTRUCTURE: Issues detected")
        print("🔧 Fix issues before proceeding to Phase 2")
    
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
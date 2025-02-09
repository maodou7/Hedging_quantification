"""
配置迁移工具
用于管理配置文件的版本和迁移
"""
import os
import json
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

logger = logging.getLogger(__name__)

class MigrationError(Exception):
    """迁移错误异常"""
    pass

class ConfigMigration:
    """配置迁移管理器"""
    
    def __init__(self, config_dir: str, backup_dir: str):
        self.config_dir = config_dir
        self.backup_dir = backup_dir
        self.version_file = os.path.join(config_dir, "version.json")
        self._migrations: Dict[str, List[Dict]] = {}
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """确保必要的目录存在"""
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def _load_version(self) -> Dict[str, str]:
        """加载配置文件版本信息"""
        if not os.path.exists(self.version_file):
            return {}
        try:
            with open(self.version_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载版本文件失败: {e}")
            return {}
    
    def _save_version(self, versions: Dict[str, str]):
        """保存配置文件版本信息"""
        try:
            with open(self.version_file, "w", encoding="utf-8") as f:
                json.dump(versions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存版本文件失败: {e}")
            raise MigrationError(f"保存版本文件失败: {e}")
    
    def _backup_config(self, config_file: str):
        """备份配置文件"""
        if not os.path.exists(config_file):
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{os.path.basename(config_file)}.{timestamp}.bak"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            shutil.copy2(config_file, backup_path)
            logger.info(f"已备份配置文件: {backup_path}")
        except Exception as e:
            logger.error(f"备份配置文件失败: {e}")
            raise MigrationError(f"备份配置文件失败: {e}")
    
    def register_migration(self, config_name: str, version: str, 
                         upgrade_func: Callable[[Dict], Dict],
                         downgrade_func: Optional[Callable[[Dict], Dict]] = None,
                         description: str = ""):
        """注册配置迁移"""
        if config_name not in self._migrations:
            self._migrations[config_name] = []
        
        self._migrations[config_name].append({
            "version": version,
            "upgrade": upgrade_func,
            "downgrade": downgrade_func,
            "description": description
        })
        
        # 按版本号排序
        self._migrations[config_name].sort(key=lambda x: x["version"])
    
    def get_pending_migrations(self, config_name: str) -> List[Dict]:
        """获取待执行的迁移"""
        current_versions = self._load_version()
        current_version = current_versions.get(config_name, "0.0.0")
        
        pending = []
        for migration in self._migrations.get(config_name, []):
            if migration["version"] > current_version:
                pending.append(migration)
        
        return pending
    
    def migrate(self, config_name: str, target_version: Optional[str] = None) -> bool:
        """执行配置迁移"""
        if config_name not in self._migrations:
            logger.warning(f"未找到{config_name}的迁移配置")
            return False
        
        current_versions = self._load_version()
        current_version = current_versions.get(config_name, "0.0.0")
        
        # 如果未指定目标版本，使用最新版本
        if target_version is None:
            target_version = self._migrations[config_name][-1]["version"]
        
        # 确定迁移方向和需要执行的迁移
        if target_version > current_version:
            migrations = [m for m in self._migrations[config_name] 
                        if current_version < m["version"] <= target_version]
            direction = "upgrade"
        else:
            migrations = [m for m in self._migrations[config_name] 
                        if target_version < m["version"] <= current_version]
            migrations.reverse()
            direction = "downgrade"
        
        if not migrations:
            logger.info(f"{config_name}已经是最新版本")
            return True
        
        # 加载配置文件
        config_file = os.path.join(self.config_dir, f"{config_name}.py")
        if not os.path.exists(config_file):
            logger.error(f"配置文件不存在: {config_file}")
            return False
        
        try:
            # 备份配置
            self._backup_config(config_file)
            
            # 执行迁移
            config_data = self._load_config(config_file)
            for migration in migrations:
                func = migration["upgrade"] if direction == "upgrade" else migration["downgrade"]
                if func is None:
                    raise MigrationError(f"未实现{direction}函数")
                
                logger.info(f"正在执行{config_name}的迁移: {migration['version']} ({migration['description']})")
                config_data = func(config_data)
            
            # 保存配置
            self._save_config(config_file, config_data)
            
            # 更新版本信息
            current_versions[config_name] = target_version
            self._save_version(current_versions)
            
            logger.info(f"{config_name}迁移完成，当前版本: {target_version}")
            return True
            
        except Exception as e:
            logger.error(f"迁移失败: {e}")
            # 尝试恢复备份
            self._restore_backup(config_file)
            raise MigrationError(f"迁移失败: {e}")
    
    def _load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 将Python配置文件转换为字典
            # 注意：这种方式可能不安全，仅用于示例
            # 实际应用中应该使用更安全的方式解析配置文件
            local_dict = {}
            exec(content, {}, local_dict)
            return local_dict
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise MigrationError(f"加载配置文件失败: {e}")
    
    def _save_config(self, config_file: str, config_data: Dict):
        """保存配置文件"""
        try:
            content = []
            for key, value in config_data.items():
                if key.startswith("__"):
                    continue
                content.append(f"{key} = {repr(value)}")
            
            with open(config_file, "w", encoding="utf-8") as f:
                f.write("\n".join(content))
                
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise MigrationError(f"保存配置文件失败: {e}")
    
    def _restore_backup(self, config_file: str):
        """恢复配置文件备份"""
        try:
            backup_files = [f for f in os.listdir(self.backup_dir) 
                          if f.startswith(os.path.basename(config_file))]
            if not backup_files:
                return
            
            # 获取最新的备份
            latest_backup = sorted(backup_files)[-1]
            backup_path = os.path.join(self.backup_dir, latest_backup)
            
            shutil.copy2(backup_path, config_file)
            logger.info(f"已恢复配置文件备份: {backup_path}")
            
        except Exception as e:
            logger.error(f"恢复备份失败: {e}")
            raise MigrationError(f"恢复备份失败: {e}")

# 示例迁移函数
def upgrade_trading_config_v1_0_0(config: Dict) -> Dict:
    """升级交易配置到1.0.0版本"""
    if "STRATEGY_CONFIG" in config:
        for strategy in config["STRATEGY_CONFIG"].values():
            if "enabled" not in strategy:
                strategy["enabled"] = False
            if "update_interval" not in strategy:
                strategy["update_interval"] = 1
    return config

def downgrade_trading_config_v1_0_0(config: Dict) -> Dict:
    """降级交易配置从1.0.0版本"""
    if "STRATEGY_CONFIG" in config:
        for strategy in config["STRATEGY_CONFIG"].values():
            strategy.pop("enabled", None)
            strategy.pop("update_interval", None)
    return config

# 创建迁移管理器实例
config_migration = ConfigMigration(
    config_dir="src/config",
    backup_dir="backups/config"
)

# 注册迁移
config_migration.register_migration(
    "trading",
    "1.0.0",
    upgrade_trading_config_v1_0_0,
    downgrade_trading_config_v1_0_0,
    "添加策略启用状态和更新间隔"
) 
"""
交易所实例管理模块

此模块提供了统一的交易所实例管理接口，支持REST API和WebSocket连接。
它封装了ccxt和ccxt.pro库的功能，提供了更简单和统一的接口来管理不同交易所的连接。

主要功能：
1. REST API实例管理
   - 创建和获取REST API连接
   - 自动进行配置管理
   - 支持自定义配置选项

2. WebSocket实例管理
   - 创建和获取WebSocket连接
   - 自动加载市场数据
   - 支持实时数据流

3. 连接生命周期管理
   - 自动管理连接的创建和销毁
   - 提供统一的清理接口
   - 错误处理和异常管理

使用示例：
    # 创建实例
    exchange_instance = ExchangeInstance()
    
    # 获取REST API连接
    rest_api = await exchange_instance.get_rest_instance('binance')
    
    # 获取WebSocket连接
    ws_api = await exchange_instance.get_ws_instance('binance')
    
    # 使用完毕后清理
    await exchange_instance.close_all()

依赖：
- ccxt: 用于REST API连接
- ccxt.pro: 用于WebSocket连接

注意：
- WebSocket连接需要在使用完毕后手动关闭
- REST API实例可以被重用
- 所有方法都提供了适当的错误处理
"""

from typing import Dict, Optional

import ccxt
import ccxt.pro as ccxtpro


class ExchangeInstance:
    """
    交易所实例管理类
    
    此类负责管理所有交易所的连接实例，包括REST API和WebSocket连接。
    它提供了一个统一的接口来创建、获取和管理这些连接。
    
    属性：
        _rest_instances (Dict[str, ccxt.Exchange]): 存储REST API实例的字典
        _ws_instances (Dict[str, ccxtpro.Exchange]): 存储WebSocket实例的字典
    
    使用示例：
        instance = ExchangeInstance()
        rest_api = await instance.get_rest_instance('binance')
        ws_api = await instance.get_ws_instance('binance')
        
        # 使用API进行操作
        markets = await rest_api.fetch_markets()
        
        # 清理连接
        await instance.close_all()
    """
    
    def __init__(self):
        """
        初始化交易所实例管理器
        
        创建用于存储REST和WebSocket实例的字典
        """
        self._rest_instances: Dict[str, ccxt.Exchange] = {}
        self._ws_instances: Dict[str, ccxtpro.Exchange] = {}

    async def get_rest_instance(self, exchange_id: str, config: Optional[dict] = None) -> ccxt.Exchange:
        """
        获取或创建REST API实例
        
        此方法会首先检查是否已存在相应的实例，如果不存在则创建新实例。
        所有实例都会使用统一的基础配置，可以通过config参数进行自定义。
        
        Args:
            exchange_id (str): 交易所标识符（例如：'binance', 'okex'等）
            config (Optional[dict]): 自定义配置字典，用于覆盖默认配置
            
        Returns:
            ccxt.Exchange: 交易所REST API实例
            
        Raises:
            Exception: 当创建实例失败时抛出异常
            
        示例：
            rest_api = await instance.get_rest_instance('binance', {
                'timeout': 15000,
                'enableRateLimit': True
            })
        """
        if exchange_id not in self._rest_instances:
            default_config = {
                'enableRateLimit': True,
                'timeout': 30000,
                'options': {
                    'defaultType': 'spot'
                }
            }

            # 合并配置
            if config:
                default_config.update(config)

            try:
                exchange_class = getattr(ccxt, exchange_id)
                self._rest_instances[exchange_id] = exchange_class(default_config)
            except Exception as e:
                raise Exception(f"创建 REST 实例失败 {exchange_id}: {str(e)}")

        return self._rest_instances[exchange_id]

    async def get_ws_instance(self, exchange_id: str, config: Optional[dict] = None) -> ccxtpro.Exchange:
        """
        获取或创建WebSocket实例
        
        此方法会首先检查是否已存在相应的WebSocket实例，如果不存在则创建新实例。
        创建后会自动加载市场数据。所有实例都使用统一的基础配置，可以通过config参数进行自定义。
        
        Args:
            exchange_id (str): 交易所标识符（例如：'binance', 'okex'等）
            config (Optional[dict]): 自定义配置字典，用于覆盖默认配置
            
        Returns:
            ccxtpro.Exchange: 交易所WebSocket实例
            
        Raises:
            Exception: 当创建实例或加载市场数据失败时抛出异常
            
        示例：
            ws_api = await instance.get_ws_instance('binance', {
                'timeout': 15000,
                'enableRateLimit': True
            })
        """
        if exchange_id not in self._ws_instances:
            default_config = {
                'enableRateLimit': True,
                'timeout': 30000,
                'options': {
                    'defaultType': 'spot'
                }
            }

            # 合并配置
            if config:
                default_config.update(config)

            try:
                ws_exchange_class = getattr(ccxtpro, exchange_id)
                ws_instance = ws_exchange_class(default_config)
                await ws_instance.load_markets()
                self._ws_instances[exchange_id] = ws_instance
            except Exception as e:
                raise Exception(f"创建 WebSocket 实例失败 {exchange_id}: {str(e)}")

        return self._ws_instances[exchange_id]

    async def close_ws_instances(self):
        """
        关闭所有WebSocket连接
        
        此方法会尝试关闭所有活动的WebSocket连接，并清理实例字典。
        如果关闭某个连接时发生错误，会打印错误信息但继续处理其他连接。
        
        示例：
            await instance.close_ws_instances()
        """
        for exchange_id, instance in self._ws_instances.items():
            try:
                await instance.close()
            except Exception as e:
                print(f"关闭 WebSocket 连接失败 {exchange_id}: {str(e)}")
        self._ws_instances.clear()

    def clear_rest_instances(self):
        """
        清除所有REST API实例
        
        此方法会清除所有REST API实例的引用。
        由于REST API实例不需要主动关闭，所以只需要清除字典即可。
        
        示例：
            instance.clear_rest_instances()
        """
        self._rest_instances.clear()

    async def close_all(self):
        """
        关闭所有连接并清理所有实例
        
        此方法是清理资源的统一接口，它会：
        1. 关闭所有WebSocket连接
        2. 清除所有REST API实例
        
        建议在程序结束时调用此方法以确保资源被正确释放。
        
        示例：
            await instance.close_all()
        """
        await self.close_ws_instances()
        self.clear_rest_instances()

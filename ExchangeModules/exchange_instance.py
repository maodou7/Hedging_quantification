from typing import Dict, Optional

import ccxt
import ccxt.pro as ccxtpro


class ExchangeInstance:
    def __init__(self):
        self._rest_instances: Dict[str, ccxt.Exchange] = {}
        self._ws_instances: Dict[str, ccxtpro.Exchange] = {}

    async def get_rest_instance(self, exchange_id: str, config: Optional[dict] = None) -> ccxt.Exchange:
        """
        获取REST API实例
        
        Args:
            exchange_id: 交易所ID
            config: 交易所配置，默认为None
            
        Returns:
            ccxt.Exchange: 交易所REST API实例
        """
        if exchange_id not in self._rest_instances:
            default_config = {
                'enableRateLimit': True,
                'timeout'        : 30000,
                'options'        : {
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
        获取WebSocket实例
        
        Args:
            exchange_id: 交易所ID
            config: 交易所配置，默认为None
            
        Returns:
            ccxtpro.Exchange: 交易所WebSocket实例
        """
        if exchange_id not in self._ws_instances:
            default_config = {
                'enableRateLimit': True,
                'timeout'        : 30000,
                'options'        : {
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
        """关闭所有WebSocket连接"""
        for exchange_id, instance in self._ws_instances.items():
            try:
                await instance.close()
            except Exception as e:
                print(f"关闭 WebSocket 连接失败 {exchange_id}: {str(e)}")
        self._ws_instances.clear()

    def clear_rest_instances(self):
        """清除所有REST实例"""
        self._rest_instances.clear()

    async def close_all(self):
        """关闭所有连接并清除实例"""
        await self.close_ws_instances()
        self.clear_rest_instances()

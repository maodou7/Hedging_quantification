"""
通知配置模块
"""
import os

NOTIFICATION_CONFIG = {
    # 邮件通知配置
    "email": {
        "enabled": True,
        "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_user": os.getenv("SMTP_USER", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        "notification_email": os.getenv("NOTIFICATION_EMAIL", ""),
        "use_tls": True,
        "templates_dir": "./templates/email",
        "rate_limit": {
            "max_emails": 100,     # 每小时最大发送数量
            "window_size": 3600    # 时间窗口（秒）
        }
    },
    
    # Telegram通知配置
    "telegram": {
        "enabled": True,
        "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        "use_proxy": False,
        "proxy_url": "",
        "templates_dir": "./templates/telegram",
        "rate_limit": {
            "max_messages": 20,    # 每分钟最大发送数量
            "window_size": 60      # 时间窗口（秒）
        }
    },
    
    # 通知级别配置
    "levels": {
        "critical": {
            "email": True,
            "telegram": True,
            "retry_count": 3,
            "retry_interval": 300  # 秒
        },
        "error": {
            "email": True,
            "telegram": True,
            "retry_count": 2,
            "retry_interval": 600
        },
        "warning": {
            "email": True,
            "telegram": False,
            "retry_count": 1,
            "retry_interval": 0
        },
        "info": {
            "email": False,
            "telegram": True,
            "retry_count": 0,
            "retry_interval": 0
        }
    },
    
    # 通知事件配置
    "events": {
        # 系统事件
        "system": {
            "startup": {
                "level": "info",
                "template": "system_startup.html"
            },
            "shutdown": {
                "level": "info",
                "template": "system_shutdown.html"
            },
            "error": {
                "level": "critical",
                "template": "system_error.html"
            }
        },
        
        # 交易事件
        "trading": {
            "new_position": {
                "level": "info",
                "template": "new_position.html"
            },
            "position_closed": {
                "level": "info",
                "template": "position_closed.html"
            },
            "stop_loss": {
                "level": "warning",
                "template": "stop_loss.html"
            },
            "take_profit": {
                "level": "info",
                "template": "take_profit.html"
            }
        },
        
        # 风险事件
        "risk": {
            "margin_call": {
                "level": "critical",
                "template": "margin_call.html"
            },
            "high_exposure": {
                "level": "warning",
                "template": "high_exposure.html"
            },
            "daily_loss_limit": {
                "level": "critical",
                "template": "daily_loss_limit.html"
            }
        },
        
        # 市场事件
        "market": {
            "high_volatility": {
                "level": "warning",
                "template": "high_volatility.html"
            },
            "low_liquidity": {
                "level": "warning",
                "template": "low_liquidity.html"
            },
            "price_anomaly": {
                "level": "warning",
                "template": "price_anomaly.html"
            }
        }
    },
    
    # 通知聚合配置
    "aggregation": {
        "enabled": True,
        "window_size": 300,  # 5分钟
        "max_events": 10,    # 每个窗口最大事件数
        "group_by": ["level", "event_type"],
        "templates": {
            "email": "aggregated_notification.html",
            "telegram": "aggregated_notification.txt"
        }
    },
    
    # 通知过滤配置
    "filters": {
        "trading": {
            "min_position_size": 100,    # USDT
            "min_profit_loss": 10,       # USDT
            "excluded_pairs": []
        },
        "market": {
            "min_volatility": 0.05,      # 5%
            "min_volume_change": 0.2,    # 20%
            "excluded_exchanges": []
        },
        "system": {
            "excluded_events": ["debug"],
            "min_severity": "warning"
        }
    }
} 
#!/usr/bin/env python3
"""
測試價外權證判斷邏輯（獨立測試，不需要依賴）
"""

import logging

# 模擬價外判斷邏輯
logger = logging.getLogger(__name__)

def is_out_of_money(moneyness_str: str) -> bool:
    """
    判斷是否為價外權證
    只要包含「價外」文字就是價外權證
    
    Args:
        moneyness_str: 價內外程度字串，例如 "價外 10.65%", "價內 5.2%", "平價"
    
    Returns:
        True 如果是價外權證，False 否則
    """
    try:
        # 簡單判斷：只要包含「價外」就是價外權證
        return '價外' in moneyness_str
        
    except (AttributeError, TypeError):
        logger.warning(f"無法解析價內外程度: {moneyness_str}")
        return False


def test_is_out_of_money():
    """測試價外判斷函數"""
    test_cases = [
        ("價外 10.65%", True, "包含價外文字應為價外"),
        ("價外 5.2%", True, "包含價外文字應為價外"),
        ("價外 0.5%", True, "包含價外文字應為價外"),
        ("價內 3.1%", False, "包含價內文字不是價外"),
        ("價內 5.8%", False, "包含價內文字不是價外"),
        ("平價", False, "平價不是價外"),
        ("0%", False, "純數字不是價外"),
        ("-5.2%", False, "負值但無價外文字不算"),
        ("+3.1%", False, "正值且無價外文字不算"),
    ]
    
    print("=" * 60)
    print("測試價外權證判斷邏輯")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for moneyness_str, expected, description in test_cases:
        result = is_out_of_money(moneyness_str)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | 輸入: {moneyness_str:>10} | 期望: {expected:>5} | 結果: {result:>5} | {description}")
    
    print("=" * 60)
    print(f"測試結果: {passed} 通過, {failed} 失敗")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = test_is_out_of_money()
    sys.exit(0 if success else 1)

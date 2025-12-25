"""
测试威胁度到震动强度的映射算法

演示新算法如何确保所有有效震动都在可感知范围内
"""

def normalize_threat_to_intensity_old(threat_scores, max_intensity=255):
    """旧算法：线性映射到 0-255"""
    if not threat_scores:
        return {i: 0 for i in range(8)}
    
    max_threat = max(threat_scores.values())
    if max_threat <= 0:
        return {i: 0 for i in range(8)}
    
    intensities = {}
    for direction_id in range(8):
        threat = threat_scores.get(direction_id, 0.0)
        normalized = threat / max_threat
        intensity = int(normalized * max_intensity)
        intensities[direction_id] = intensity
    
    return intensities


def normalize_threat_to_intensity_new(
    threat_scores, 
    min_intensity=80, 
    max_intensity=255,
    threshold=0.01
):
    """新算法：映射到 min_intensity-max_intensity，确保可感知"""
    if not threat_scores:
        return {i: 0 for i in range(8)}
    
    max_threat = max(threat_scores.values())
    if max_threat <= 0:
        return {i: 0 for i in range(8)}
    
    intensities = {}
    for direction_id in range(8):
        threat = threat_scores.get(direction_id, 0.0)
        
        if threat < threshold:
            intensities[direction_id] = 0
        else:
            normalized = threat / max_threat
            intensity = int(min_intensity + normalized * (max_intensity - min_intensity))
            intensities[direction_id] = intensity
    
    return intensities


def print_comparison(threat_scores, scenario_name):
    """打印对比结果"""
    print("\n" + "=" * 80)
    print(f"场景：{scenario_name}")
    print("=" * 80)
    
    print("\n威胁度分数：")
    for direction_id in range(8):
        threat = threat_scores.get(direction_id, 0.0)
        direction_name = ["正前", "前右", "正右", "后右", "正后", "后左", "正左", "前左"][direction_id]
        print(f"  方向{direction_id}（{direction_name}）: {threat:.4f}")
    
    # 旧算法结果
    old_intensities = normalize_threat_to_intensity_old(threat_scores)
    print("\n【旧算法】线性映射到 0-255：")
    for direction_id in range(8):
        intensity = old_intensities.get(direction_id, 0)
        threat = threat_scores.get(direction_id, 0.0)
        direction_name = ["正前", "前右", "正右", "后右", "正后", "后左", "正左", "前左"][direction_id]
        perceptible = "✓ 可感知" if intensity >= 80 else "✗ 感觉不到"
        print(f"  方向{direction_id}（{direction_name}）: 强度={intensity:3d} {perceptible}")
    
    # 新算法结果
    new_intensities = normalize_threat_to_intensity_new(threat_scores, min_intensity=80)
    print("\n【新算法】映射到 80-255（最低可感知阈值=80）：")
    for direction_id in range(8):
        intensity = new_intensities.get(direction_id, 0)
        threat = threat_scores.get(direction_id, 0.0)
        direction_name = ["正前", "前右", "正右", "后右", "正后", "后左", "正左", "前左"][direction_id]
        if intensity > 0:
            perceptible = "✓ 可感知"
        else:
            perceptible = "○ 无震动"
        print(f"  方向{direction_id}（{direction_name}）: 强度={intensity:3d} {perceptible}")
    
    print("\n" + "-" * 80)
    print("对比分析：")
    old_perceptible_count = sum(1 for i in old_intensities.values() if i >= 80)
    new_perceptible_count = sum(1 for i in new_intensities.values() if i > 0)
    print(f"  旧算法：{old_perceptible_count}/8 个方向可感知")
    print(f"  新算法：{new_perceptible_count}/8 个方向可感知（所有非零震动都可感知）")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("威胁度到震动强度映射算法对比测试")
    print("=" * 80)
    
    # 场景1：主要威胁在前方，侧面有次要威胁
    scenario1 = {
        0: 0.85,  # 正前：高威胁
        1: 0.32,  # 前右：中等威胁
        2: 0.15,  # 正右：低威胁
        3: 0.08,  # 后右：很低威胁
        4: 0.00,  # 正后：无威胁
        5: 0.00,  # 后左：无威胁
        6: 0.12,  # 正左：低威胁
        7: 0.25   # 前左：中低威胁
    }
    print_comparison(scenario1, "前方高威胁，多个方向有次要威胁")
    
    # 场景2：多个中等威胁分散在各个方向
    scenario2 = {
        0: 0.45,  # 正前
        1: 0.38,  # 前右
        2: 0.30,  # 正右
        3: 0.25,  # 后右
        4: 0.20,  # 正后
        5: 0.18,  # 后左
        6: 0.35,  # 正左
        7: 0.40   # 前左
    }
    print_comparison(scenario2, "威胁分散在多个方向，没有特别突出的")
    
    # 场景3：一个超高威胁，其他都很低
    scenario3 = {
        0: 0.95,  # 正前：超高威胁
        1: 0.10,  # 前右：很低
        2: 0.05,  # 正右：极低
        3: 0.02,  # 后右：微弱
        4: 0.00,  # 正后：无
        5: 0.00,  # 后左：无
        6: 0.03,  # 正左：微弱
        7: 0.08   # 前左：很低
    }
    print_comparison(scenario3, "正前方一个极高威胁，其他方向威胁极低")
    
    print("\n" + "=" * 80)
    print("总结：")
    print("=" * 80)
    print("【旧算法问题】")
    print("  - 线性映射到 0-255，导致低威胁方向的强度 < 80（不可感知）")
    print("  - 用户只能感受到高威胁方向，失去了完整的态势感知")
    print()
    print("【新算法优势】")
    print("  - 所有有效震动都映射到 80-255 范围")
    print("  - 确保用户能感知到所有威胁方向")
    print("  - 仍然保持相对强度差异，最高威胁=255，其他按比例")
    print("  - 极低威胁（< threshold）直接过滤，不震动")
    print()
    print("【推荐配置】")
    print("  - MIN_PERCEPTIBLE_INTENSITY = 80  # 根据实际硬件测试调整（60-100）")
    print("  - MAX_VIBRATION_INTENSITY = 255  # 最大强度")
    print("  - THREAT_THRESHOLD = 0.01        # 低于此值不震动")
    print("=" * 80)






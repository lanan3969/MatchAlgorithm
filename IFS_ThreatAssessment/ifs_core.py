"""
直觉模糊集（Intuitionistic Fuzzy Set, IFS）核心数学库

参考论文：
《地面作战目标威胁评估多属性指标处理方法》
孔德鹏, 常天庆, 郝娜, 张雷, 郭理彬
自动化学报, 2021, 47(1): 161-172

实现内容：
1. IFS基本定义和数据结构
2. 多种数据类型到IFS的转换方法
3. IFS运算（距离度量、得分函数、比较法则）
"""

import numpy as np
from typing import Tuple, Union, List
from dataclasses import dataclass
import math


@dataclass
class IFS:
    """
    直觉模糊数（Intuitionistic Fuzzy Number）
    
    三元组 (μ, ν, π)：
    - μ (mu): 隶属度 [0, 1]，表示"属于"的程度
    - ν (nu): 非隶属度 [0, 1]，表示"不属于"的程度
    - π (pi): 犹豫度 [0, 1]，表示不确定性程度
    
    约束条件：μ + ν ≤ 1, π = 1 - μ - ν
    """
    mu: float      # 隶属度 (membership degree)
    nu: float      # 非隶属度 (non-membership degree)
    pi: float = None  # 犹豫度 (hesitancy degree)，自动计算
    
    def __post_init__(self):
        """验证IFS约束条件并计算犹豫度"""
        # 确保在有效范围内
        self.mu = max(0.0, min(1.0, self.mu))
        self.nu = max(0.0, min(1.0, self.nu))
        
        # 约束条件：μ + ν ≤ 1
        if self.mu + self.nu > 1.0:
            # 归一化处理
            total = self.mu + self.nu
            self.mu = self.mu / total
            self.nu = self.nu / total
        
        # 计算犹豫度
        self.pi = 1.0 - self.mu - self.nu
    
    def score(self) -> float:
        """
        得分函数 S(A) = μ - ν
        
        论文公式：用于比较两个IFS的大小
        返回值范围：[-1, 1]
        - 越接近1表示威胁度越高
        - 越接近-1表示威胁度越低
        """
        return self.mu - self.nu
    
    def accuracy(self) -> float:
        """
        精确函数 H(A) = μ + ν
        
        论文公式：用于当得分函数相等时的辅助判断
        返回值范围：[0, 1]
        - 越接近1表示确定性越高
        - 越接近0表示不确定性越高
        """
        return self.mu + self.nu
    
    def __str__(self) -> str:
        return f"IFS(μ={self.mu:.3f}, ν={self.nu:.3f}, π={self.pi:.3f})"
    
    def __repr__(self) -> str:
        return self.__str__()


class IFSConverter:
    """IFS转换器：将不同类型的数据转换为直觉模糊数"""
    
    @staticmethod
    def from_real_number(value: float, ideal: float, tolerance: float, 
                        min_val: float = None, max_val: float = None) -> IFS:
        """
        实数 → IFS（论文方法1）
        
        使用高斯隶属函数：
        μ = exp(-(value - ideal)² / (2 * tolerance²))
        
        Args:
            value: 实际值
            ideal: 理想值（最优值）
            tolerance: 容忍度（标准差）
            min_val: 最小可能值（用于计算非隶属度）
            max_val: 最大可能值（用于计算非隶属度）
        
        Returns:
            IFS对象
        """
        # 计算隶属度（高斯函数）
        mu = math.exp(-((value - ideal) ** 2) / (2 * tolerance ** 2))
        
        # 计算非隶属度
        if min_val is not None and max_val is not None:
            # 基于偏离理想值的程度
            range_span = max_val - min_val
            deviation = abs(value - ideal)
            nu = min(0.9, deviation / range_span) if range_span > 0 else 0.1
            # 确保 μ + ν ≤ 1
            if mu + nu > 1.0:
                nu = 1.0 - mu - 0.05  # 保留小量犹豫度
        else:
            # 简化计算：ν = 1 - μ - π，假设π = 0.1
            nu = max(0.0, 1.0 - mu - 0.1)
        
        return IFS(mu=mu, nu=nu)
    
    @staticmethod
    def from_interval(lower: float, upper: float, ideal: float, 
                     reference_range: Tuple[float, float]) -> IFS:
        """
        区间数 → IFS（论文方法2）
        
        基于区间的中点和半径：
        - 中点越接近理想值，μ越大
        - 区间越宽，π越大（不确定性高）
        
        Args:
            lower: 区间下界
            upper: 区间上界
            ideal: 理想值
            reference_range: 参考范围 (min, max)
        
        Returns:
            IFS对象
        """
        # 区间中点
        midpoint = (lower + upper) / 2.0
        # 区间半径（宽度的一半）
        radius = (upper - lower) / 2.0
        
        # 参考范围
        ref_min, ref_max = reference_range
        ref_span = ref_max - ref_min
        
        # 计算隶属度（基于中点接近理想值的程度）
        if ref_span > 0:
            deviation = abs(midpoint - ideal) / ref_span
            mu = math.exp(-2 * deviation)
        else:
            mu = 1.0 if midpoint == ideal else 0.5
        
        # 计算犹豫度（基于区间宽度）
        if ref_span > 0:
            pi = min(0.5, radius / ref_span)  # 犹豫度最大0.5
        else:
            pi = 0.1
        
        # 计算非隶属度
        nu = 1.0 - mu - pi
        
        return IFS(mu=mu, nu=nu)
    
    @staticmethod
    def from_triangular_fuzzy(a: float, b: float, c: float,
                             reference_range: Tuple[float, float]) -> IFS:
        """
        三角模糊数 → IFS（论文方法3）
        
        三角模糊数 (a, b, c)：
        - a: 最小可能值
        - b: 最可能值（核心值）
        - c: 最大可能值
        
        Args:
            a: 左端点
            b: 核心值
            c: 右端点
            reference_range: 参考范围
        
        Returns:
            IFS对象
        """
        # 隶属度：基于核心值b的位置
        ref_min, ref_max = reference_range
        ref_span = ref_max - ref_min
        
        if ref_span > 0:
            # 核心值在参考范围中的相对位置
            relative_pos = (b - ref_min) / ref_span
            mu = 1.0 - abs(relative_pos - 0.5) * 2  # 中间值最大
        else:
            mu = 0.5
        
        # 犹豫度：基于三角形的宽度
        width = c - a
        if ref_span > 0:
            pi = min(0.4, width / ref_span)
        else:
            pi = 0.2
        
        # 非隶属度
        nu = 1.0 - mu - pi
        
        return IFS(mu=mu, nu=nu)
    
    @staticmethod
    def from_linguistic_term(term: str) -> IFS:
        """
        模糊评价语言 → IFS（论文方法4）
        
        预定义的语言术语集及其IFS表示
        
        Args:
            term: 语言术语（如"极高"、"高"、"中"等）
        
        Returns:
            IFS对象
        """
        # 论文表3：模糊评价语言的IFS表示
        linguistic_mapping = {
            # 中文术语
            '极高': IFS(0.95, 0.02),
            '很高': IFS(0.85, 0.10),
            '高': IFS(0.75, 0.15),
            '较高': IFS(0.65, 0.25),
            '中': IFS(0.50, 0.40),
            '较低': IFS(0.35, 0.55),
            '低': IFS(0.25, 0.65),
            '很低': IFS(0.15, 0.75),
            '极低': IFS(0.05, 0.90),
            
            # 英文术语
            'very_high': IFS(0.90, 0.05),
            'high': IFS(0.75, 0.15),
            'medium_high': IFS(0.65, 0.25),
            'medium': IFS(0.50, 0.40),
            'medium_low': IFS(0.35, 0.55),
            'low': IFS(0.25, 0.65),
            'very_low': IFS(0.10, 0.80),
            
            # 威胁等级
            'critical': IFS(0.95, 0.02),
            'high_threat': IFS(0.80, 0.12),
            'moderate': IFS(0.55, 0.35),
            'low_threat': IFS(0.30, 0.60),
            'minimal': IFS(0.10, 0.85),
        }
        
        term_lower = term.lower().strip()
        if term_lower in linguistic_mapping:
            return linguistic_mapping[term_lower]
        
        # 默认返回中等威胁
        return IFS(0.50, 0.40)


class IFSOperations:
    """IFS运算操作类"""
    
    @staticmethod
    def hamming_distance(ifs1: IFS, ifs2: IFS) -> float:
        """
        Hamming距离（论文公式）
        
        d_H(A, B) = (|μ_A - μ_B| + |ν_A - ν_B| + |π_A - π_B|) / 2
        
        返回值范围：[0, 1]
        """
        return (abs(ifs1.mu - ifs2.mu) + 
                abs(ifs1.nu - ifs2.nu) + 
                abs(ifs1.pi - ifs2.pi)) / 2.0
    
    @staticmethod
    def euclidean_distance(ifs1: IFS, ifs2: IFS) -> float:
        """
        Euclidean距离（论文公式）
        
        d_E(A, B) = sqrt((μ_A - μ_B)² + (ν_A - ν_B)² + (π_A - π_B)²) / sqrt(2)
        
        返回值范围：[0, 1]
        """
        squared_diff = ((ifs1.mu - ifs2.mu) ** 2 + 
                       (ifs1.nu - ifs2.nu) ** 2 + 
                       (ifs1.pi - ifs2.pi) ** 2)
        return math.sqrt(squared_diff / 2.0)
    
    @staticmethod
    def compare(ifs1: IFS, ifs2: IFS) -> int:
        """
        比较两个IFS的大小（论文比较法则）
        
        规则：
        1. 首先比较得分函数 S(A) = μ - ν
        2. 若得分相等，则比较精确函数 H(A) = μ + ν
        
        Returns:
            1: ifs1 > ifs2
            0: ifs1 == ifs2
            -1: ifs1 < ifs2
        """
        score1 = ifs1.score()
        score2 = ifs2.score()
        
        # 得分阈值（考虑浮点误差）
        epsilon = 1e-6
        
        if abs(score1 - score2) > epsilon:
            return 1 if score1 > score2 else -1
        else:
            # 得分相等，比较精确度
            acc1 = ifs1.accuracy()
            acc2 = ifs2.accuracy()
            
            if abs(acc1 - acc2) > epsilon:
                return 1 if acc1 > acc2 else -1
            else:
                return 0
    
    @staticmethod
    def weighted_average(ifs_list: List[IFS], weights: List[float]) -> IFS:
        """
        IFS加权算术平均算子（IFWA）（论文公式7-9）
        
        IFWA(A₁, A₂, ..., Aₙ) = (μ_w, ν_w)
        其中：
        μ_w = Σ(w_i × μ_i)
        ν_w = Σ(w_i × ν_i)
        
        Args:
            ifs_list: IFS列表
            weights: 权重列表（应归一化，和为1）
        
        Returns:
            加权平均后的IFS
        """
        if len(ifs_list) != len(weights):
            raise ValueError("IFS列表和权重列表长度必须相等")
        
        # 归一化权重
        weight_sum = sum(weights)
        if weight_sum == 0:
            raise ValueError("权重和不能为0")
        normalized_weights = [w / weight_sum for w in weights]
        
        # 计算加权平均
        mu_weighted = sum(w * ifs.mu for w, ifs in zip(normalized_weights, ifs_list))
        nu_weighted = sum(w * ifs.nu for w, ifs in zip(normalized_weights, ifs_list))
        
        return IFS(mu=mu_weighted, nu=nu_weighted)
    
    @staticmethod
    def complement(ifs: IFS) -> IFS:
        """
        IFS的补集
        
        A^c = (ν, μ, π)
        """
        return IFS(mu=ifs.nu, nu=ifs.mu)
    
    @staticmethod
    def union(ifs1: IFS, ifs2: IFS) -> IFS:
        """
        IFS的并集
        
        A ∪ B = (max(μ_A, μ_B), min(ν_A, ν_B))
        """
        return IFS(mu=max(ifs1.mu, ifs2.mu), 
                  nu=min(ifs1.nu, ifs2.nu))
    
    @staticmethod
    def intersection(ifs1: IFS, ifs2: IFS) -> IFS:
        """
        IFS的交集
        
        A ∩ B = (min(μ_A, μ_B), max(ν_A, ν_B))
        """
        return IFS(mu=min(ifs1.mu, ifs2.mu), 
                  nu=max(ifs1.nu, ifs2.nu))


# 便捷函数
def create_ifs(mu: float, nu: float) -> IFS:
    """创建IFS对象的便捷函数"""
    return IFS(mu=mu, nu=nu)


def convert_to_ifs(value: Union[float, Tuple, str], 
                   conversion_type: str = 'real',
                   **kwargs) -> IFS:
    """
    通用转换函数
    
    Args:
        value: 待转换的值
        conversion_type: 转换类型 ('real', 'interval', 'triangular', 'linguistic')
        **kwargs: 额外参数
    
    Returns:
        IFS对象
    """
    converter = IFSConverter()
    
    if conversion_type == 'real':
        return converter.from_real_number(value, **kwargs)
    elif conversion_type == 'interval':
        lower, upper = value
        return converter.from_interval(lower, upper, **kwargs)
    elif conversion_type == 'triangular':
        a, b, c = value
        return converter.from_triangular_fuzzy(a, b, c, **kwargs)
    elif conversion_type == 'linguistic':
        return converter.from_linguistic_term(value)
    else:
        raise ValueError(f"不支持的转换类型: {conversion_type}")


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("直觉模糊集（IFS）核心库测试")
    print("=" * 60)
    
    # 测试1：基本IFS创建
    print("\n【测试1】基本IFS创建：")
    ifs1 = IFS(0.7, 0.2)
    print(f"IFS1: {ifs1}")
    print(f"得分函数: {ifs1.score():.3f}")
    print(f"精确函数: {ifs1.accuracy():.3f}")
    
    # 测试2：实数转IFS
    print("\n【测试2】实数转IFS（距离30米，理想值0米）：")
    distance_ifs = IFSConverter.from_real_number(
        value=30, ideal=0, tolerance=15, min_val=0, max_val=50
    )
    print(f"距离IFS: {distance_ifs}")
    
    # 测试3：语言术语转IFS
    print("\n【测试3】模糊评价语言转IFS：")
    for term in ['极高', '高', '中', '低', '极低']:
        ifs_term = IFSConverter.from_linguistic_term(term)
        print(f"{term}: {ifs_term} (得分={ifs_term.score():.3f})")
    
    # 测试4：IFS比较
    print("\n【测试4】IFS比较：")
    ifs_high = IFSConverter.from_linguistic_term('高')
    ifs_low = IFSConverter.from_linguistic_term('低')
    comparison = IFSOperations.compare(ifs_high, ifs_low)
    print(f"高威胁 vs 低威胁: {comparison} ({'高威胁更大' if comparison > 0 else '相等' if comparison == 0 else '低威胁更大'})")
    
    # 测试5：加权平均
    print("\n【测试5】IFS加权平均（多指标综合）：")
    ifs_distance = IFS(0.8, 0.1)  # 距离威胁
    ifs_speed = IFS(0.6, 0.3)     # 速度威胁
    ifs_type = IFS(0.9, 0.05)     # 类型威胁
    
    weights = [0.4, 0.3, 0.3]  # 距离、速度、类型的权重
    ifs_combined = IFSOperations.weighted_average(
        [ifs_distance, ifs_speed, ifs_type], weights
    )
    print(f"综合威胁IFS: {ifs_combined}")
    print(f"综合威胁得分: {ifs_combined.score():.3f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")


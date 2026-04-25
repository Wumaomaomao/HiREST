#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import csv
import shutil

def extract_system_name(exec_file):
    """从exec文件名中提取系统名称"""
    base_name = os.path.basename(exec_file)
    if '_' in base_name:
        return base_name.split('_')[0]
    else:
        return base_name.split('.')[0]

def calculate_coverage(csv_file):
    """计算Branch、Line和Method的覆盖率"""
    total_branch_missed = 0
    total_branch_covered = 0
    total_line_missed = 0
    total_line_covered = 0
    total_method_missed = 0
    total_method_covered = 0
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_branch_missed += int(row['BRANCH_MISSED'])
            total_branch_covered += int(row['BRANCH_COVERED'])
            total_line_missed += int(row['LINE_MISSED'])
            total_line_covered += int(row['LINE_COVERED'])
            total_method_missed += int(row['METHOD_MISSED'])
            total_method_covered += int(row['METHOD_COVERED'])
    
    branch_coverage = 0 if (total_branch_missed + total_branch_covered) == 0 else \
                     total_branch_covered / (total_branch_missed + total_branch_covered) * 100
    
    line_coverage = 0 if (total_line_missed + total_line_covered) == 0 else \
                   total_line_covered / (total_line_missed + total_line_covered) * 100
    
    method_coverage = 0 if (total_method_missed + total_method_covered) == 0 else \
                     total_method_covered / (total_method_missed + total_method_covered) * 100
    
    return {
        'branch_coverage': branch_coverage,
        'line_coverage': line_coverage,
        'method_coverage': method_coverage
    }

def main():
    if len(sys.argv) < 2:
        print("使用方法: python jacoco_analyzer.py <exec文件路径>")
        sys.exit(1)
    
    exec_file = sys.argv[1]
    if not os.path.exists(exec_file):
        print(f"错误: 文件 {exec_file} 不存在")
        sys.exit(1)
    
    # 提取系统名称
    system_name = extract_system_name(exec_file)
    print(f"系统名称: {system_name}")
    
    # 检查系统文件夹是否存在
    if not os.path.exists(system_name):
        print(f"错误: 系统文件夹 {system_name} 不存在")
        sys.exit(1)
    
    # 检查classfiles目录是否存在
    classfiles_dir = os.path.join(system_name, "classfiles")
    if not os.path.exists(classfiles_dir):
        print(f"错误: classfiles目录 {classfiles_dir} 不存在")
        sys.exit(1)
    
    # 生成CSV文件名
    csv_file = exec_file.replace('.exec', '.csv')
    # 生成结果文件名
    result_file = exec_file.replace('.exec', '.txt')
    
    # 使用jacococli.jar生成CSV报告
    cmd = [
        'java', '-jar', 'jacococli.jar', 'report', 
        exec_file, 
        '--csv', csv_file, 
        '--classfiles', classfiles_dir
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"生成CSV报告时出错: {e}")
        sys.exit(1)
    
    
    # 计算覆盖率
    coverage = calculate_coverage(csv_file)
    
    print("\n覆盖率统计:")
    print(f"Branch 覆盖率: {coverage['branch_coverage']:.2f}%")
    print(f"Line 覆盖率: {coverage['line_coverage']:.2f}%")
    print(f"Method 覆盖率: {coverage['method_coverage']:.2f}%")
    
    # 将覆盖率结果写入txt文件
    with open(result_file, 'w') as f:
        f.write(f"Branch 覆盖率: {coverage['branch_coverage']:.2f}%\n")
        f.write(f"Line 覆盖率: {coverage['line_coverage']:.2f}%\n")
        f.write(f"Method 覆盖率: {coverage['method_coverage']:.2f}%\n")

    # 创建coverage_data/SYSTEMNAME目录
    coverage_dir = os.path.join("requests_coverage_data", system_name)
    os.makedirs(coverage_dir, exist_ok=True)
    
    # 移动exec和csv文件到coverage_data/SYSTEMNAME目录
    exec_dest = os.path.join(coverage_dir, os.path.basename(exec_file))
    csv_dest = os.path.join(coverage_dir, os.path.basename(csv_file))
    result_dest = os.path.join(coverage_dir, os.path.basename(result_file))
    
    shutil.move(exec_file, exec_dest)
    shutil.move(csv_file, csv_dest)
    shutil.move(result_file, result_dest)
    
    print(f"文件已移动到 {coverage_dir} 目录")

if __name__ == "__main__":
    main()
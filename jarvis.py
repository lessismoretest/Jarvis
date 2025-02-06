#!/usr/bin/env python3

"""
Jarvis - 个人智能助手系统
基于钢铁侠电影中的 J.A.R.V.I.S. (Just A Rather Very Intelligent System)
"""

class Jarvis:
    def __init__(self):
        """
        初始化 Jarvis 系统
        """
        self.name = "Jarvis"
    
    def greet(self):
        """
        Jarvis 的问候语
        """
        print(f"Hello world! 我是 {self.name}, 很高兴为您服务。")

def main():
    """
    主程序入口
    """
    jarvis = Jarvis()
    jarvis.greet()

if __name__ == "__main__":
    main() 
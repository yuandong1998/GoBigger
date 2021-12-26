"""

ref:https://github.com/opendilab/GoBigger/blob/main/gobigger/agents/bot_agent.py
"""

import os
import random
import logging
import copy
import queue
from pygame.math import Vector2

from .base_agent import BaseAgent


class RuleAgent(BaseAgent):
    '''
    Overview:
        A simple script bot
    '''
    def __init__(self, name=None, level=3):
        self.name = name
        self.actions_queue = queue.Queue()
        self.last_clone_num = 1
        self.last_total_size = 0
        self.level = level
        self.team_name = None
        self.attack_target = None
        
    def step(self, obs):
        return self.process1(obs)


    def process1(self, obs):
        ## 如果队列中有动作，执行
        if self.actions_queue.qsize() > 0:
            return self.actions_queue.get()

        ## 对obs进行处理
        self.team_name = obs['team_name']
        
        overlap = obs['overlap']
        overlap = self.preprocess_overlap(overlap)

        my_clone_balls,my_team_clone_balls,others_clone_balls = self.process_clone_balls(overlap['clone'])
        min_distance_food, min_food_ball = self.process_food_balls(overlap['food'], my_clone_balls[0])
        min_distance_thorns, min_thorns_ball = self.process_thorns_balls(overlap['thorns'], my_clone_balls[0])

        #如果我的克隆球数量大于9，并且第4个大的半径大于14：中吐
        if len(my_clone_balls) >= 9 and my_clone_balls[4]['radius'] > 14: 
            return self.eject2Center()
        #如果我的小于其他人的：逃跑
        elif self.run_away(my_clone_balls,others_clone_balls): 
            pass
        #如果比其他的大则追击
        elif self.attack(my_clone_balls,others_clone_balls):
            pass
        # 那么吃最近的刺，分裂
        elif min_thorns_ball is not None:
            return self.eat_thorn(my_clone_balls,min_thorns_ball)
        else:
            return self.eat_food(my_clone_balls,min_food_ball)
        action_ret = self.actions_queue.get()
        return action_ret


    def process_clone_balls(self, clone_balls):
        """
        处理overlap中clone balls的信息,返回安装radius排序后的
        my_clone_balls: 玩家自己的clone ball列表
        my_team_clone_balls: 玩家队伍除了自己以外的clone balll列表
        others_clone_balls: 其他队伍的clone balll列表
        """
        my_clone_balls,my_team_clone_balls,others_clone_balls = [],[],[]

        for clone_ball in clone_balls:# 遍历视野内所有的分身球
            if clone_ball['player'] == self.name:# 找到属于自己的分身球
                my_clone_balls.append(copy.deepcopy(clone_ball))
            elif clone_ball['team']==self.team_name: #属于自己队伍的分身球
                my_team_clone_balls.append(copy.deepcopy(clone_ball))
            else:
                others_clone_balls.append(copy.deepcopy(clone_ball))

        # 按半径从大到小进行排序
        my_clone_balls.sort(key=lambda a: a['radius'], reverse=True) 
        my_team_clone_balls.sort(key=lambda a: a['radius'], reverse=True) 
        others_clone_balls.sort(key=lambda a: a['radius'], reverse=True)
        
        return my_clone_balls,my_team_clone_balls,others_clone_balls

    def process_thorns_balls(self, thorns_balls, my_max_clone_ball):
        """
            return:
                min_thorns_ball: 距离当前最大的球的最近的刺
                min_distance: min_thorns_ball的距离
        """
        min_distance = 10000
        min_thorns_ball = None
        for thorns_ball in thorns_balls:
            if thorns_ball['radius'] < my_max_clone_ball['radius']: #如果我当前最大的球的半径大于刺的半径
                distance = (thorns_ball['position'] - my_max_clone_ball['position']).length() #我与刺的距离
                if distance < min_distance:
                    min_distance = distance
                    min_thorns_ball = copy.deepcopy(thorns_ball)
        return min_distance, min_thorns_ball

    def process_food_balls(self, food_balls, my_max_clone_ball):
        """
            return:
                min_food_ball: 距离当前最大的球的最近食物
                min_distance: min_food_ball的距离
        """
        min_distance = 10000
        min_food_ball = None
        for food_ball in food_balls:
            distance = (food_ball['position'] - my_max_clone_ball['position']).length()
            if distance < min_distance:
                min_distance = distance
                min_food_ball = copy.deepcopy(food_ball)
        return min_distance, min_food_ball

    def preprocess_overlap(self, overlap):
        """
            处理obs中的overlap信息，将每个种类的每一个生成一个字典。
            clone包含'position','radius','player','team'信息
            其他包含'position','radius'信息
        """
        new_overlap = {}
        for k, v in overlap.items():
            if k =='clone':
                new_overlap[k] = []
                for index, vv in enumerate(v):
                    tmp={}
                    tmp['position'] = Vector2(vv[0],vv[1]) 
                    tmp['radius'] = vv[2]
                    tmp['player'] = str(int(vv[-2]))
                    tmp['team'] = str(int(vv[-1]))
                    new_overlap[k].append(tmp)
            else:
                new_overlap[k] = []
                for index, vv in enumerate(v):
                    tmp={}
                    tmp['position'] = Vector2(vv[0],vv[1])
                    tmp['radius'] = vv[2]
                    new_overlap[k].append(tmp)
        return new_overlap

    
    def add_noise_to_direction(self, direction, noise_ratio=0.1):
        direction = direction + Vector2(((random.random() * 2 - 1)*noise_ratio)*direction.x, ((random.random() * 2 - 1)*noise_ratio)*direction.y)
        return direction

    #####################################################################################################
    #####################################################################################################
    ###########################################高级动作###################################################
    #####################################################################################################
    #####################################################################################################


    def eject2Center(self):
        """"high-level operation:Eject towards the center"""
        self.actions_queue.put([None, None, 2]) # 使用停止技能
        self.actions_queue.put([None, None, -1]) # 不操作，等待球球聚集
        self.actions_queue.put([None, None, -1])
        self.actions_queue.put([None, None, -1])
        self.actions_queue.put([None, None, -1])
        self.actions_queue.put([None, None, -1])
        self.actions_queue.put([None, None, -1])
        self.actions_queue.put([None, None, 0]) # 使用吐孢子球技能
        self.actions_queue.put([None, None, 0])
        self.actions_queue.put([None, None, 0])
        self.actions_queue.put([None, None, 0])
        self.actions_queue.put([None, None, 0])
        self.actions_queue.put([None, None, 0])
        self.actions_queue.put([None, None, 0])
        self.actions_queue.put([None, None, 0])
        action_ret = self.actions_queue.get()
        return action_ret

    def run_away(self,my_clone_balls,others_clone_balls):
        """run away from"""
        if len(others_clone_balls) > 0 and len(my_clone_balls)>0 and my_clone_balls[-1]['radius'] <others_clone_balls[0]['radius'] and my_clone_balls[0]['radius']>others_clone_balls[0]['radius']:
            self.actions_queue.put([None, None, 2]) # 使用停止技能
            self.actions_queue.put([None, None, -1]) # 不操作，等待球球聚集
            self.actions_queue.put([None, None, -1])
            self.actions_queue.put([None, None, -1])
            self.actions_queue.put([None, None, -1])
            self.actions_queue.put([None, None, -1])
            self.actions_queue.put([None, None, -1])
            self.actions_queue.put([None, None, 0]) # 使用吐孢子球技能
            self.actions_queue.put([None, None, 0])
            self.actions_queue.put([None, None, 0])
            self.actions_queue.put([None, None, 0])
            self.actions_queue.put([None, None, 0])
            self.actions_queue.put([None, None, 0])
            self.actions_queue.put([None, None, 0])
            self.actions_queue.put([None, None, 0])
            return True
        elif len(others_clone_balls) > 0 and my_clone_balls[0]['radius'] < others_clone_balls[0]['radius']:
            direction = (my_clone_balls[0]['position'] - others_clone_balls[0]['position']).normalize()
            action_type = -1
            self.actions_queue.put([direction.x, direction.y, action_type])
            return True
        else:
            return False
    
    def eat_food(self,my_clone_balls,min_food_ball):
        """eat food"""
        if my_clone_balls[0]['radius']<27:
            direction = (Vector2(500,500)-my_clone_balls[0]['position']).normalize() #向中心靠拢
        if min_food_ball is not None:
            direction = (min_food_ball['position'] - my_clone_balls[0]['position']).normalize()
        else:
            direction = (Vector2(0, 0) - my_clone_balls[0]['position']).normalize()
        action_type = -1
        self.actions_queue.put([direction.x, direction.y, action_type])
        action_ret = self.actions_queue.get()
        return action_ret

    def eat_thorn(self,my_clone_balls,min_thorns_ball):
        direction = (min_thorns_ball['position'] - my_clone_balls[0]['position']).normalize()
        action_type = -1
        self.actions_queue.put([direction.x, direction.y, action_type])
        action_ret = self.actions_queue.get()
        return action_ret

    
    def attack(self,my_clone_balls,others_clone_balls):
        """
        攻击，如果可以攻击返回True,否则返回False
        我们只对可以在一次分裂或者两次分裂可以吃的的进行攻击
        """
        coef1=2.5
        coef2=5
        if len(others_clone_balls)==0 or my_clone_balls[0]['radius']*0.5<others_clone_balls[0]['radius']:
            return False
        
        radius=my_clone_balls[0]['radius']#玩家最大球的半径
        target = None
        candidate = None
        for ball in others_clone_balls:
            dist=(ball['position']-my_clone_balls[0]['position']).length()
            if dist<radius*coef1: 
                target=ball
                break
            elif not candidate and dist<radius*coef2:
                candidate=ball
        if target is None and candidate is None:
            return False
        elif not target is None:
            direction = (target['position'] - my_clone_balls[0]['position']).normalize()
            action_type = 4
            self.actions_queue.put([direction.x, direction.y, action_type])
            return True
        else:
            direction = (candidate['position'] - my_clone_balls[0]['position']).normalize()
            action_type = 4
            self.actions_queue.put([direction.x, direction.y, action_type])
            self.actions_queue.put([direction.x, direction.y, action_type])
            return True
        return False

        

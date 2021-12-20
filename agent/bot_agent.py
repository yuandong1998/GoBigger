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


class BotAgentNew(BaseAgent):
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
        # self.team_name = None
        
    def step(self, obs):
        if self.level == 1:
            return self.step_level_1(obs)
        if self.level == 2:
            return self.step_level_2(obs)
        if self.level == 3:
            return self.step_level_3(obs)

    def step_level_1(self, obs):
        """
        首先找食物，如果没有就吃自己的小球
        """
        if self.actions_queue.qsize() > 0: #如果动作队列里还有动作没有执行则直接执行
            return self.actions_queue.get()
        overlap = obs['overlap']
        overlap = self.preprocess(overlap)
        food_balls = overlap['food']
        thorns_balls = overlap['thorns']
        spore_balls = overlap['spore']
        clone_balls = overlap['clone']

        my_clone_balls, others_clone_balls = self.process_clone_balls(clone_balls)
        min_distance, min_food_ball = self.process_food_balls(food_balls, my_clone_balls[0])        
        if min_food_ball is not None: #首先找食物
            direction = (min_food_ball['position'] - my_clone_balls[0]['position']).normalize()
        else: #如果没有吃自己的小球
            direction = (Vector2(0, 0) - my_clone_balls[0]['position']).normalize()
        action_type = -1
        self.actions_queue.put([direction.x, direction.y, action_type])
        action_ret = self.actions_queue.get()
        return action_ret

    def step_level_2(self, obs):
        if self.actions_queue.qsize() > 0:
            return self.actions_queue.get()
        overlap = obs['overlap']
        overlap = self.preprocess(overlap)
        food_balls = overlap['food']
        thorns_balls = overlap['thorns']
        spore_balls = overlap['spore']
        clone_balls = overlap['clone']

        my_clone_balls, others_clone_balls = self.process_clone_balls(clone_balls)
        min_distance, min_thorns_ball = self.process_thorns_balls(thorns_balls, my_clone_balls[0])
        if min_thorns_ball is not None:
            direction = (min_thorns_ball['position'] - my_clone_balls[0]['position']).normalize() #吃小的荆棘球
        else:
            direction = (Vector2(0, 0) - my_clone_balls[0]['position']).normalize()
        action_type = -1
        self.actions_queue.put([direction.x, direction.y, action_type])
        self.actions_queue.put([None, None, -1])# 不操作，等待球球聚集
        self.actions_queue.put([None, None, -1])
        self.actions_queue.put([None, None, -1])
        self.actions_queue.put([None, None, -1])
        self.actions_queue.put([None, None, -1])
        action_ret = self.actions_queue.get()
        return action_ret

    def step_level_3(self, obs):
        if self.actions_queue.qsize() > 0:
            return self.actions_queue.get()

        self.team_name = obs['team_name']
        
        overlap = obs['overlap']
        overlap = self.preprocess(overlap)
        food_balls = overlap['food']
        thorns_balls = overlap['thorns']
        spore_balls = overlap['spore']
        clone_balls = overlap['clone']
        

        my_clone_balls, others_clone_balls = self.process_clone_balls(clone_balls)
        if len(my_clone_balls) >= 9 and my_clone_balls[4]['radius'] > 14: #如果我的克隆球数量大于9，并且第4个大的半径大于14：中吐
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

        if len(others_clone_balls) > 0 and my_clone_balls[0]['radius'] < others_clone_balls[0]['radius']: #如果我的小于其他人的：逃跑
            direction = (my_clone_balls[0]['position'] - others_clone_balls[0]['position']).normalize()
            action_type = -1
            
        elif len(others_clone_balls) > 0 and my_clone_balls[0]['radius'] > others_clone_balls[0]['radius']+500:
            direction = (others_clone_balls[0]['position'] - my_clone_balls[0]['position']).normalize()
            action_type = -1

        else:
            min_distance, min_thorns_ball = self.process_thorns_balls(thorns_balls, my_clone_balls[0]) #否则吃最近的刺
            if min_thorns_ball is not None:
                direction = (min_thorns_ball['position'] - my_clone_balls[0]['position']).normalize()
            else:
                min_distance, min_food_ball = self.process_food_balls(food_balls, my_clone_balls[0]) #再否则吃食物
                if my_clone_balls[0]['radius']<27:
                    direction = (Vector2(500,500)-my_clone_balls[0]['position']).normalize() #向中心靠拢
                if min_food_ball is not None:
                    direction = (min_food_ball['position'] - my_clone_balls[0]['position']).normalize()
                else:
                    direction = (Vector2(0, 0) - my_clone_balls[0]['position']).normalize()
            action_random = random.random() #加入随机动作
            if action_random < 0.02:
                action_type = 1
            if action_random < 0.04 and action_random > 0.02:
                action_type = 2
            else:
                action_type = -1
        direction = self.add_noise_to_direction(direction) #动嘴加入噪声
        self.actions_queue.put([direction.x, direction.y, action_type])
        action_ret = self.actions_queue.get()
        return action_ret

    def process_clone_balls(self, clone_balls):
        my_clone_balls = []
        others_clone_balls = []
        for clone_ball in clone_balls:# 遍历视野内所有的分身球
            if clone_ball['player'] == self.name:# 找到属于自己的分身球
                my_clone_balls.append(copy.deepcopy(clone_ball))
        my_clone_balls.sort(key=lambda a: a['radius'], reverse=True) # 按半径从大到小进行排序

        for clone_ball in clone_balls: #找到属于其他玩家的分身球
            # if clone_ball['player'] != self.name:
            if clone_ball['team']!=self.team_name:
                others_clone_balls.append(copy.deepcopy(clone_ball))
        others_clone_balls.sort(key=lambda a: a['radius'], reverse=True)
        return my_clone_balls, others_clone_balls

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

    def preprocess(self, overlap):
        """
            处理obs中的overlap信息。
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

    def preprocess_tuple2vector(self, overlap):
        new_overlap = {}
        for k, v in overlap.items():
            new_overlap[k] = []
            for index, vv in enumerate(v):
                new_overlap[k].append(vv)
                new_overlap[k][index]['position'] = Vector2(*vv['position'])
        return new_overlap
    
    def add_noise_to_direction(self, direction, noise_ratio=0.1):
        direction = direction + Vector2(((random.random() * 2 - 1)*noise_ratio)*direction.x, ((random.random() * 2 - 1)*noise_ratio)*direction.y)
        return direction
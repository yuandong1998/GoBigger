"""


"""

import os
import random
import logging
import copy
import queue
from pygame.math import Vector2

from .base_agent import BaseAgent


class BotAgent(BaseAgent):
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
        self.team_name=None

    def step(self, obs):
        pass


    def process(self, obs):
        overlap = obs['overlap']
        
        
    def fleeAction(self, obs):
        """
        看见比自己大的逃跑
        """
        pass


    def eatFoodAction(self, obs):
        """
        吃食物
        """
        pass

    def eatplayerAction(self, obs):
        """
        吃其他玩家
        """
        pass


    
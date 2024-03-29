import os
import sys
import logging
import importlib
import time
import argparse
import requests
import subprocess
from tqdm import tqdm

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
os.environ['SDL_AUDIODRIVER'] = 'dsp'

from gobigger.agents import BotAgent
from gobigger.utils import Border
from gobigger.server import Server
from gobigger.render import RealtimeRender, RealtimePartialRender, EnvRender

logging.basicConfig(level=logging.DEBUG)

def eval_once(cfg):
    server = Server(dict(
            team_num=4, # 队伍数量
            player_num_per_team=3, # 每个队伍的玩家数量
            # match_time=60*10, # 每场比赛的持续时间
    ))
    render = EnvRender(server.map_width, server.map_height)
    server.set_render(render)
    server.start()
    agents = []
    team_player_names = server.get_team_names()
    team_names = list(team_player_names.keys())

    for index in range(0,server.team_num):
        p = importlib.import_module('{}.my_submission'.format(cfg.players[index]))
        agents.append(p.MySubmission(team_name=team_names[index], 
                                         player_names=team_player_names[team_names[index]]))
        # try:
        #     p = importlib.import_module('{}.my_submission'.format(cfg.players[index]))
        #     agents.append(p.MySubmission(team_name=team_names[index], 
        #                                  player_names=team_player_names[team_names[index]]))
        # except Exception as e:
        #     print('You must implement `MySubmission` in my_submission.py !')
        #     exit()
    
    for i in range(server.match_time*server.action_tick_per_second):
        obs = server.obs()
        global_state, player_states = obs
        actions = {}
        for agent in agents:
            agent_obs = [global_state, {
                player_name: player_states[player_name] for player_name in agent.player_names
            }]
            actions.update(agent.get_actions(agent_obs))
        finish_flag = server.step(actions=actions)
        if finish_flag:
            logging.debug('Game Over!')
            break
    ##查看global_state中的leaderboard
    print(global_state['leaderboard'])
    winner=max(global_state['leaderboard'], key=global_state['leaderboard'].get)
    print("winner:",winner)
    server.close()
    return winner


from multiprocessing import Pool

def eval(cfg):
    win_rate=dict()
    for i in range(4):
        win_rate[str(i)]=0
    # for i in range(cfg.EVAL_TIME):
    #     winner=eval_once(cfg)
    #     win_rate[winner]=win_rate.get(winner,0)+1

    p=Pool(10)
    res=p.map(eval_once,[cfg for _ in range(10)])
    for winner in res:
        win_rate[winner]=win_rate.get(winner,0)+1
    
    output=""
    for p in range(len(cfg.players)):
        output+=cfg.players[p]+":"+str(win_rate.get(str(p),0)/cfg.EVAL_TIME)
    print(output)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--EVAL_TIME', type=int,default=10)
    args = parser.parse_args()
    args.players=['ruleAgent','botAgent','botAgent','botAgent'] #players
    eval(args)
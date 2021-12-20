# from gobigger.agents import BotAgent
from agent.bot_agent import BotAgentNew
from gobigger.agents import BotAgent
from gobigger.server import Server
from gobigger.render import EnvRender
from dibaselinev1.my_submission import MySubmission

def launch_a_game():
    server = Server(dict(
        match_time=60*5,
        save_video=False,
        save_quality='low', # 保存的录像质量。默认为high，可以是low
        save_path='./video', # 保存录像路径。默认为空
    )) # server的默认配置就是标准的比赛setting

    render = EnvRender(server.map_width, server.map_height) # 引入渲染模块
    server.set_render(render) # 设置渲染模块
    server.reset() # 初始化游戏引擎
    
    bot_agents = [] # 用于存放本局比赛中用到的所有bot

    flag=0
    for players in server.player_manager.get_player_names_with_team():
        for player in players:
            if flag==0:
                bot_agents.append(BotAgentNew(player, level=3))
            else:
                bot_agents.append(BotAgent(player, level=3))
            flag+=1

    for player in server.player_manager.get_players():
        bot_agents.append(BotAgentNew(player.name, level=3)) # 初始化每个bot，注意要给每个bot提供队伍名称和玩家名称 

    for i in range(100000):
        # 获取到返回的环境状态信息
        obs = server.obs()
        # 动作是一个字典，包含每个玩家的动作
        # print(obs[0])
        actions = {bot_agent.name: bot_agent.step(obs[1][bot_agent.name]) for bot_agent in bot_agents}
        finish_flag = server.step(actions=actions) # 环境执行动作
        print('{} {:.4f} leaderboard={}'.format(i, server.last_time, obs[0]['leaderboard']))
        if finish_flag:
            print('Game Over')
            break
    server.close()

if __name__=="__main__":
    launch_a_game()
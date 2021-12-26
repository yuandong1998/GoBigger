# AI球球大作战
dibaselinev1和dibaselinev2是主办方提供的强化学习baseline，BotAgent是官方的规则baseline。

## TODO LIST 
[x] 完成不同agent之间胜率的测试程序

[x] ruleAgent的attack优化 

## BotAgent的漏洞
* BotAgent 逃跑是以最大的反方向逃跑，所以可以采用包夹。
* BotAgent 不对spore进行处理
* 中吐时不躲避

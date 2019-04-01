1、运行lsscsi -g 命令，查看盘符，修改config.txt文件里对应的各个配置项内容，请仔细配置。
       【注意】：不要看成系统盘。
2、将脚本VdbenchRunner.py和config.txt以及测试用例excel和run.sh放到某个目录下，这个目录可以随意。
       【注意】：文件需要解密上传才可使用。
3、运行脚本，执行以下命令：./run.sh。通过tmux a -t test 查看脚本执行现场，看有没有报错
       【注意】： 查看运行可通过tmux a -t test 查看脚本执行现场，看有没有报错。crtl+d 退出tmux，回到shell。
4、测试执行完成，根据收到的邮件，下载测试结果及时查看测试数据以及生成的html效果图。








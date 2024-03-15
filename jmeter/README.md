## linux命令
- 每隔0.1秒刷新一次显存使用情况
    ```shell
    watch -n 0.1 -d nvidia-smi
    ```
- 0.5s刷新一次
	```shell
    top -d 0.5
	```
- 实时查看某个进程的情况
	```shell
    top -p pid
	```
- 查看某个进程的内存占用
	```shell
    ps -p pid -o rss= | awk '{ printf "%.2f MB\n", $1 / 1024 }'
	```




	
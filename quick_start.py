import subprocess
import os
import datetime

services = [
    # "scs",
    # "restcountries",
    #  "languagetool",
    # "ncs",
    # "news",
    # "petstore",
    # "youtube",
    # "person",
      "user"
     # "genome"
    # "project"
]

time_limit = 3600
requests = 100000000

def run_fuzzing(service, time_limit, requests):
    cmd = [
        "python", "-m", "examples.fuzzing",
        "--service", service,
        "--time_limit", str(time_limit),
        "--requests", str(requests),
        # "--exec-log-only"
        "--no-log"
    ]
    # 后台执行，输出丢弃
    with open(os.devnull, "w") as devnull:
        process = subprocess.Popen(cmd, stdout=devnull, stderr=devnull)
        # process.wait()

if __name__ == "__main__":
    if os.fork() > 0:
        # 父进程退出，子进程在后台执行
        exit(0)
    # 子进程依次执行每个服务
    for service in services:
        print(f"Start fuzzing: {service}, parameters: time_limit={time_limit}, requests={requests}")
        run_fuzzing(service, time_limit, requests)
        print(f"Finish fuzzing: {service}")
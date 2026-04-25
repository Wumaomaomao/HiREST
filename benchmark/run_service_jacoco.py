import os, time, argparse, subprocess

from datetime import datetime

# global dir config

autoresttest_path = "/root/autoresttest"
Languagetool_path = "/root/languagetool"


jdk8_1_service_path = f"{autoresttest_path}/aratrl-service/jdk8_1"
jdk8_2_service_path = f"{autoresttest_path}/aratrl-service/jdk8_2"
jdk11_service_path = f"{autoresttest_path}/aratrl-service/jdk11"
youtube_path = f"{autoresttest_path}/services/youtube"

javaagent_path = "/root/HiREST/scripts/org.jacoco.agent-0.8.7-runtime.jar"
service_log_path = os.path.join(os.path.dirname(__file__), "service_logs/")
languagetool_path = f"{Languagetool_path}/languagetool-standalone/target/LanguageTool-6.8-SNAPSHOT/LanguageTool-6.8-SNAPSHOT"

# 服务配置
SERVICES = {
    "person": {
        "jacoco_agent_port": 8090,
        "exec_path": f"{jdk8_2_service_path}/person-controller/target/java-spring-boot-mongodb-starter-1.0.0.jar",
        "exec_type": "jar",
        "server_port": "50111",
        "jdk_version": "8",
        "database": {
            "ports": {"27019": "27017"},
            "container": "mongodb",
            "image": "mongo:5.0.9",
            "args" : "--replSet rs0"
        }
    },
    "scs": {
        "jacoco_agent_port": 8091,
        "exec_path": f"{jdk8_1_service_path}/em/embedded/rest/scs",
        "main_class": "em.embedded.org.restscs.RunServer",
        "exec_type": "class",
        "server_port": "50108",
        "jdk_version": "8",
    },
    "news":{
        "jacoco_agent_port": 8092,
        "exec_path": "/root/services/REST_Go/services/evo_jdk8/em/embedded/rest/news",
        "main_class": "em.embedded.org.tsdes.RunServer",
        "exec_type": "class",
        "server_port": "50103",
        "jdk_version": "8",
    },
    "youtube":{
        "jacoco_agent_port": 8094,
        "exec_path": f"{youtube_path}/target/youtubemock-sut.jar --server.port=9009",
        "exec_type": "jar",
        "server_port": "9009",
        "jdk_version": "11",
    },
    "restcountries": {
        "jacoco_agent_port": 8097,
        "exec_path": f"{jdk8_1_service_path}/em/embedded/rest/restcountries",
        "main_class": "em.embedded.eu.fayder.RunServer",
        "exec_type": "class",
        "server_port": "50106",
        "jdk_version": "8",
    },
    "languagetool": {
        "jacoco_agent_port": 8098,
        "exec_path": languagetool_path,
        "main_class": "languagetool-server.jar org.languagetool.server.HTTPServer",
        "exec_type": "class",
        "exec_params": "--port 49981 --public --allow-origin",
        "server_port": "49981",
        "jdk_version": "17",
    },
    "ncs": {
        "jacoco_agent_port": 8099,
        "exec_path": f"{jdk8_1_service_path}/em/embedded/rest/ncs",
        "main_class": "em.embedded.org.restncs.RunServer",
        "exec_type": "class",
        "server_port": "50102",
        "jdk_version": "8",
    },
    "genome": {
        "jacoco_agent_port": 8101,
        "exec_path": f"{jdk8_2_service_path}/genome-nexus/web/target/web-0-unknown-version-SNAPSHOT.war",
        "exec_type": "jar",
        "server_port": "50110",
        "jdk_version": "8",
        "database"  :{
            "ports": {"27018": "27017"},
            "container": "mongodb_geonome",
            "image": "gn-mongo:1.0",
        }
    },
    "user" : {
        "jacoco_agent_port": 8102,
        "exec_path": f"{jdk8_2_service_path}/user-management/target/microdemo2-1.0.0-SNAPSHOT.jar",
        "exec_type": "jar",
        "server_port": "50115",
        "jdk_version": "8",
        "database": {
            "ports": {"3306": "3306"},
            "container": "mysql_user",
            "image": " -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=users mysql:latest",
        }
    },
    "project": {
        "jacoco_agent_port": 8103,
        "exec_path": f"{jdk11_service_path}/project-tracking-system/target/project-tracking-system.jar",
        "exec_type": "jar",
        "server_port": "50118",
        "jdk_version": "11",
    }
}


def load_jdk_env(version: str) -> bool:
    """Load JDK environment variables for the specified version."""
    env_file = os.path.join(os.path.dirname(__file__), "jdk.env")
    if not os.path.exists(env_file):
        print(f"JDK environment file not found: {env_file}")
        return False

    # 使用 subprocess 执行 `. ./jdk.env {version}`
    command = f". {env_file} {version} && env"
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, executable="/bin/bash"
    )

    if result.returncode != 0:
        print(f"Failed to load JDK environment for version {version}: {result.stderr}")
        return False

    return True


def build_javaagent_args(port: int) -> str:
    """construct javaagent args"""
    return f"-javaagent:{javaagent_path}=includes=*,output=tcpserver,address=*,port={port},dumponexit=true -Dfile.encoding=UTF-8"


def start_database(config: dict):
    """start database if required"""
    image = config["image"]
    ports = config["ports"]
    container = config["container"]

    port_args = " ".join(
        [f"-p {host}:{container}" for host, container in ports.items()]
    )

    # Check if the database is already running

    check_cmd = f"docker ps -q -a -f name={container}"
    check_result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)

    if check_result.stdout.strip():
        print(f"Database container: {container} is already running, try to kill it...")
        kill_cmd = f"sudo docker rm -f {container}"
        kill_result = subprocess.run(
            kill_cmd, shell=True, capture_output=True, text=True
        )
        if kill_result.returncode != 0:
            print(f"Failed to kill container {container}: {kill_result.stderr}")
            exit(-1)
        print(f"Container {container} killed successfully.")
    if config.get("args"):
        start_cmd = f"sudo docker run -d --name {container} {port_args} {image} --replSet rs0"
    else:
        start_cmd = f"sudo docker run -d --name {container} {port_args} {image}"

    # sudo docker exec -it mongodb mongosh
    # rs.initiate()

    print(f"Starting database container: {container} with command: {start_cmd}")
    start_result = subprocess.run(start_cmd, shell=True, capture_output=True, text=True)
    print(f"Waiting for {container} to start...120s")
    time.sleep(120)
    if start_result.returncode != 0:
        print(f"Failed to start container {container}: {start_result.stderr}")
        exit(-1)

    print(f"Container {container} started successfully.")

    # 执行 rs.initiate()
    if config.get("args"):
        print(f"Initializing replica set for container {container}...")
        exec_cmd = f"sudo docker exec -it {container} mongosh --eval 'rs.initiate()'"
        exec_result = subprocess.run(exec_cmd, shell=True, capture_output=True, text=True)
        if exec_result.returncode != 0:
            print(f"Failed to initialize replica set for {container}: {exec_result.stderr}")
            exit(-1)

        print(f"Replica set initialized successfully for container {container}.")


def start_service(service_name: str):
    """start service with jacoco by service name"""
    if service_name not in SERVICES:
        print(f"Service {service_name} not found, only support {list(SERVICES.keys())}")
        return

    service = SERVICES[service_name]
    server_port = str(service.get("server_port", "")).split('/')[0]

    if server_port and server_port != "0":
        # Check if the service port is already in use
        port_check_cmd = f"lsof -i :{server_port}"
        port_check = subprocess.run(port_check_cmd, shell=True, capture_output=True, text=True)

        # if service is running, kill it
        if port_check.returncode == 0:
            print(f"Port {service['server_port']} is in use. Attempting to kill existing process...")
            # Extract PID from lsof output and kill the process
            pid = port_check.stdout.split('\n')[1].split()[1]
            kill_cmd = f"kill -9 {pid}"
            subprocess.run(kill_cmd, shell=True)
            print(f"Killed process {pid}")
            time.sleep(2)  # Wait for port to be released
            print(f"Port {service['server_port']} is now free.")

    if "database" in service:
        # start database if required
        start_database(service["database"])

    # Load JDK environment for the specified version
    if not load_jdk_env(service["jdk_version"]):
        print("Failed to load JDK environment. Aborting service start.")
        return

    # construct java agent args
    javaagent_args = build_javaagent_args(service["jacoco_agent_port"])

    # construct service log path
    service_log_dir = os.path.join(
        os.path.dirname(__file__), "service_logs", service_name
    )
    os.makedirs(service_log_dir, exist_ok=True)

    service_log_filepath = os.path.join(
        os.path.dirname(__file__), "service_logs", service_name,
        f"{service_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    )

    # construct command
    if service["exec_type"] == "jar":
        if service_name == "graphhopper":
            cmd = (
                f"nohup java -Djdk.attach.allowAttachSelf=true -Djdk.net.preferIPv4Stack=true "
                f"{javaagent_args} {service['exec_params']} -jar {service['exec_path']} >> {service_log_filepath} 2>&1 &"
            )
        else:
            cmd = (
                f"nohup java -Djdk.attach.allowAttachSelf=true -Djdk.net.preferIPv4Stack=true "
                f"{javaagent_args} -jar {service['exec_path']} >> {service_log_filepath} 2>&1 &"
            )
    elif service["exec_type"] == "class":
        if service_name == "languagetool":
            cmd = (
                f"cd {service['exec_path']} && "
                f"nohup java -Djdk.attach.allowAttachSelf=true -Djdk.net.preferIPv4Stack=true "
                f"{javaagent_args} -cp {service['main_class']} {service['exec_params']} >> {service_log_filepath} 2>&1 &"
            )
        else:
            cmd = (
                f"cd {service['exec_path']} && "
                f"nohup java -Djdk.attach.allowAttachSelf=true -Djdk.net.preferIPv4Stack=true "
                f"{javaagent_args} -cp target/classes:target/test-classes:$(cat cp.txt) {service['main_class']} "
                f">> {service_log_filepath} 2>&1 &"
            )
    elif service["exec_type"] == "maven":
        env_cmd = service.get("exec_env", "")
        env_prefix = f"env {env_cmd} " if env_cmd else ""
        cmd = f"cd {service['exec_path']} && \
        nohup {env_prefix} mvn {service['exec_params']} >> {service_log_filepath} 2>&1 &"
    else:
        print(f"Unknown service type for {service_name}")
        return

    print(
        f"Starting service {service_name} on port {service.get('server_port', 'unknown')} with jacoco agent on port {service['jacoco_agent_port']}"
        f"\nService logs will be saved to {service_log_filepath}"
    )
    print(cmd)

    try:
        ret = subprocess.run(cmd, shell=True, check=True)
        print(f"Service {service_name} started successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to start service {service_name}: {e}")
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="run jvm service with jacoco agent...")
    parser.add_argument("service", help="service name to run", type=str)
    args = parser.parse_args()
    start_service(args.service)

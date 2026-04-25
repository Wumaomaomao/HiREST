# HiREST

Replication Package for the paper: **Hierarchical Input Space Partition guided
Fuzzing for REST APIs**

# QuickStart
## Environment Setup
### HiREST Repository
You need download this repo and navigate to its root directory:
```bash
cd /path/to/HiREST
```
### Python Environment
**Requirement**: Use Python 3.10.16. We strongly recommend using a **virtual environment**.
Install the project in editable mode:
```bash
pip install -e .
```
### Configure Environment Variables
Create a `.env` file in the project root with the following content:
```
OPENAI_API_KEY=<openai_api_key>
OPENAI_BASE_URL=<openai_base_url>
```

## Reproduction
HiREST contains two phase:
1. `Initialization Phase`(offline, with LLMs) 
2. `Testing Phase`(Online, request the services).

### Initialization Phase (Offline)
Offline results for supported services are pre-generated and located in `./apis/{service_name}/`.
```
HiREST
├── apis
│   ├── youtube
│   │   ├── op_slide/ # Operation documentation with inter-parameter constraints
│   │   ├── partition/ # Generated API and Parameter input spaces
│   │   ├── seed/ #  Test seed 
│   │   └── spec/ # Input OpenAPI specification 
│   ├── ...
├── hirest # the core library of HiREST 
```


### Testing Phase
After confirming initialization results exist, and the REST services of [REST_Go](https://github.com/codingsoo/REST_Go/blob/master/setup.sh) and [YouTube](https://github.com/codingsoo/LlamaRestTest/blob/main/setup.sh) have been running.

```bash
python examples/fuzzing.py --service <service_name> --requests <max_requests> --time_limit <max_time_limit_in_seconds>
```
for example:
```bash
python examples/fuzzing.py --service scs --requests 1000
```
* You can know which REST services is support in dict `SERVICES` in file `./examples/fuzzing.py`.

The output files are located in `./apis/{service_name}/`.

**Run Initialization Demo (Optional)**:
To understand the initialization workflow with a API, you can execute:
```bash
python examples/offline/offline.py --input_path ./apis/demo/spec/scs.yaml
```

# Setup a new target SUT
If you further setup a new target sut for hirest, you need pay attention to:

## Intialization phase
1. Prerequisite: Target service must have an OpenAPI specification (v3.0+).
2. Place the specification (JSON/YAML) in ./apis/{your_service_name}/spec/.
3. Run the initialization script as described above.

## Testing phase
1. After successful initialization, configure the `service_name` and `base_url` in `./examples/fuzzing.py`.
2. Start testing using the `fuzzing.py`.
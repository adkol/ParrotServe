Our project is stored on the michigan-bigdata-PG0 shared folder on CloudLab. The full directory is /proj/michigan-bigdata-PG0/groups/parrot. This directory contains the ParrotServe repository and a miniconda folder that contains a conda environment with all the required dependencies pre-installed.

https://github.com/adkol/ParrotServe/tree/submission this branch includes our changes. There is no need to clone the repository if using cloudlab Wisconsin

Start an experiment with nodes that have a GPU with compute capability >= 7.0.
You can run this system on one node or more, we ran our experiments with 3 nodes.

We recommend using Cloudlab Wisconsin with d7525 nodes since that is what all our tests have been on.
Resize file system steps
You must resize the file system for every node you use. 

sudo cfdisk /dev/sda (or the drive that holds the root filesystem)
delete all partitions except sda1
then resize sda1 to 256 gb
then create 2 new partitions of size 3gb each and one new partition of the remaining size
set the types of these partitions to Empty, Linux Swap, and Empty
write this out to the disk file
quit
sudo reboot
sudo resize2fs /dev/sda1 (if /dev/sda1 holds the root filesystem, otherwise use the partition that holds the root filesystem)
you can check the new size of sda1 with the “df” command and it should be resized

A tutorial on cfdisk can be found here. 
Dependency Installation steps
The conda environment in the shared folder already contains all the dependencies preinstalled. Otherwise follow the directions listed here.

Setup steps

Perform this on every node
copy the setup.sh file from the git repo 
chmod +x setup.sh
./setup.sh

Perform this on every terminal
sudo -i
cd /proj/michigan-bigdata-PG0/groups/parrot/
source miniconda3/bin/activate
conda activate parrot
cd ParrotServe
source .env

Run Experiment

Before running any script in the experiment make sure to perform the setup steps in every terminal used

To start the server run this command, the server must be started no node0, edit the config file if network topology is different
python3 -m parrot.serve.http_server --config_path sample_configs/core/localhost_serve_core.json --log_dir log

Start one engine on the same node as the server with this command, the engine must be started no node0, edit the config file if network topology is different
python3 -m parrot.engine.http_server --config_path sample_configs/engine/vicuna-7b-v1.3.json --log_dir log


It is optional to start more engine instances on other nodes. 
Here are commands to start engines on node 1 and node2
node1:
python3 -m parrot.engine.http_server --config_path sample_configs/engine/vicuna-7b-v1.3_remote.json --log_dir log_node1/ --engine_name node1_server

node2:
python3 -m parrot.engine.http_server --config_path sample_configs/engine/vicuna-7b-v1.3_node2.json --log_dir log_node2/ --engine_name node2_server


You can modify the delay threshold in global_scheduler.py as well as turn delay scheduling on or off by the global variables at the top. 
For example you can run with these parameters
MAX_DELAY_THRESHOLD = 800
DELAY_SCHEDULING_ON = True

then run
python3 smalltest.py 
for a simple test with two requests where only the second request benefits from prefix sharing

and you can also run a more intensive test :

python3 async_questions_latency_profiling_more_prefixes.py


you can view our logs in the saved_logs folder
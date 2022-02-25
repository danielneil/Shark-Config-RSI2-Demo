#!/usr/bin/python3

# Process the yaml configuration file, so we can regenerate it into native Nagios configuration.

import yaml
import os
from datetime import datetime

##############################################################    
from io import StringIO

class StringBuilder:

    _file_str = None

    def __init__(self):
        self._file_str = StringIO()

    def Add(self, str):
        self._file_str.write(str)

    def __str__(self):
        return self._file_str.getvalue()

##############################################################    
# Master process loop
def process_instrument_config(i_data):

    instrument = i_data['instrument']
    group = i_data['group']

    hosts.Add("\ndefine host {\n")
    hosts.Add("\tuse instrument\n")
    hosts.Add("\thost_name " + instrument + "\n")
    hosts.Add("\thostgroups " + group + "\n")
    hosts.Add("\tcheck_command check_price\n")
    hosts.Add("\taddress 127.0.0.1" + "\n")
    hosts.Add("}\n")
        
    WriteLogFile("Created instrument: " + instrument)

    hostGroups.append(str(group))

    # Process the list of plugins,
    process_plugin_config(i_data['plugin'], instrument)

##############################################################    
# Process the plugins
def process_plugin_config(p_data, instrument):
	
	global total_capital
	global total_shares

	for plugins in p_data:
		
		services.Add("\ndefine service {\n")
		services.Add("\tuse generic-service\n")
	
		serv_grp = ""
		cmd_name = ""
		cmd_desc = ""
		cmd_args = StringBuilder();
		backtest_cmd_args = StringBuilder();
		backtestFileName = ""

		for argName, argValue in plugins.items():

			if argName == "group":
				serviceGroups.append(str(argValue))
				serv_grp = str(argValue)
			elif argName == "name":
				cmd_name = argValue
			elif argName == "desc":
				cmd_desc = argValue
			else:
				arg_str = "!" + str(argValue)
				cmd_args.Add(arg_str)

				if plugins["name"] == "backtest": 

					if argName == "file":
						backtestFileName = argValue
					else:
						backtest_cmd_args.Add("--" + argName + "=" + str(argValue) + " ")
						
					if argName == "capital":
						total_capital += int(argValue)
						
					if argName == "shares":
						total_shares += int (argValue)
						

		services.Add("\thost_name " + instrument + "\n")
		services.Add("\tservice_description " + cmd_desc + "\n")

		# If this is a back test, we need to write the arguments to a script file.

		if plugins["name"] == "backtest":

			scriptFile = "/shark/.tmp/backtest.scriptFile." + str(instrument)

			with open(scriptFile, "w") as f:

				f.write("--ticker=" + str(instrument) + "\n")
				splits = str(backtest_cmd_args).split()

				for btarg in splits:

					f.write(btarg + "\n")

			services.Add("\tcheck_command " + cmd_name + "!" + backtestFileName + "!" + scriptFile + "\n")
			services.Add("\taction_url /framework/public/index.php/BacktestReport?ticker=" + instrument + "\n")
		else:
			services.Add("\tcheck_command " + cmd_name + "!" + str(instrument) + str(cmd_args) + "\n")

		services.Add("\tservicegroups " + serv_grp + "\n")
		services.Add("}\n")
		
		WriteLogFile("Attached plugin: " + cmd_name)

##############################################################    
# Log file - records a log of the config gen for the web interface.
def WriteLogFile(string):

    now = datetime.now()

    dt_string = now.strftime("%b %d %H:%M:%S")

    with open(logFile, "a") as f:
        f.write(dt_string  + " " + string + "\n")

		
##############################################################    
# Process the yaml file - main entry point.
hosts = StringBuilder();
hostGroups = []
serviceGroups = []
services = StringBuilder();

# Portfolio info
total_capital = 0
total_shares = 0


# log file - if it exists, delete.
logFile = "/shark/log/config_gen.log"
if os.path.exists(logFile):
    os.remove(logFile)

WriteLogFile("Starting - Reading yaml file")

with open ("/shark/Shark-Config/config/files/trading-config.yml", "r") as f:

    # Load YAML data from the file

    data = yaml.safe_load(f)

    # Iterate the loop to read and print YAML data

    for i in range(len(data)):

        process_instrument_config(data[i])

##############################################################    
# Print the hosts group configuration.
sorted_host_groups = sorted(set(hostGroups))

for ig in sorted_host_groups:

    WriteLogFile("Created instrument group: " + ig)

    print ("\ndefine hostgroup {")
    print ("\thostgroup_name " + ig )
    print ("\talias " + ig )
    print ("}")

##############################################################    
# Print the service groups
sorted_service_groups = sorted(set(serviceGroups))

for sg in sorted_service_groups:

    WriteLogFile("Created plugin group: " + sg)

    print("\ndefine servicegroup {")
    print("\tservicegroup_name " + sg)
    print("\talias " + sg)
    print("}")

##############################################################    
# Print the hosts configuration.
print (hosts)

##############################################################
# Print the services
print (services)

# Finished!
WriteLogFile("Finished")
